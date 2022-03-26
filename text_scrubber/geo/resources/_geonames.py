# Geonames data downloaded from http://www.geonames.org/,
# Geonames is distributed under a Creative Commons Attribution 4.0 License:
# http://download.geonames.org/export/dump/readme.txt
#
# mkdir geonames && cd geonames
# wget -r -np -nd -A.zip http://download.geonames.org/export/dump/
# unzip "*.zip" (replace all readme files)
# rm *.zip
# cd alternatenames
# unzip "*.zip" (replace all readme files)
# rm *.zip

import argparse
import os
import re
import unicodedata
from functools import partial, reduce
from typing import Callable, Dict, List, Tuple

import pandas as pd
from tqdm.auto import tqdm

from text_scrubber.geo import clean_city, clean_region

try:
    from mpire import WorkerPool
    MPIRE_AVAILABLE = True
except ImportError:
    WorkerPool = None
    MPIRE_AVAILABLE = False

RE_ALPHA = re.compile(r'[a-zA-Z]')


def process_country(filename: str, work_dir: str, save_dir_cities: str, save_dir_regions: str,
                    manual_alternate_names: Dict[str, Dict[str, List[str]]]) -> None:
    """
    Processes a single country file and stores the results to file, one for cities, one for regions.

    :param filename: Filename
    :param work_dir: Working directory
    :param save_dir_cities: Save directory for cities
    :param save_dir_regions: Save directory for regions
    :param manual_alternate_names: {country code: {city: list of manually added alternate names}}
    """
    manual_alternate_names = manual_alternate_names.get(filename[:2], {})

    columns = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude', 'feature class',
               'feature code', 'country code', 'cc2', 'admin1 code', 'admin2 code', 'admin3 code', 'admin4 code',
               'population', 'elevation', 'dem', 'timezone', 'modification date']
    df = pd.read_csv(os.path.join(work_dir, filename), sep='\t', header=None, names=columns,
                     usecols=['geonameid', 'name', 'asciiname', 'feature class', 'feature code'], keep_default_na=False)

    # Change exotic single quotes to regular single quote and remove any commas
    df['name'] = df['name'].apply(clean_punctuation)

    # Replace name by asciiname when it's not in Latin alphabet. We keep the alternate names in non-Latin, that's fine
    df['name'] = df[['name', 'asciiname']].apply(
        lambda row_: row_['name'] if is_latin(row_['name']) else row_['asciiname'], axis=1
    )

    # Only retain useful populated places for cities
    df_cities = df[(df['feature class'] == 'P') &
                   ~df['feature code'].isin({'PPLCH', 'PPLH', 'PPLL', 'PPLQ', 'PPLR', 'PPLW', 'PPLX'})]

    # Obtain regions. A=country, state, region,...; H=stream, lake, ...; L=parks, area, ...;
    # T=mountain, hill, rock, ...; V=forest, heath, ...
    df_regions = df[df['feature class'].isin({'A', 'H', 'L', 'T', 'V'})]

    # Add alternate names for cities and regions
    df_cities, df_regions = add_alternate_names(work_dir, df_cities, df_regions, filename)

    # Remove duplicate names and drop columns that are no longer of interest
    df_cities = remove_duplicates(df_cities)
    df_regions = remove_duplicates(df_regions)

    # Save to file
    manual_alternate_names = manual_alternate_names.get(filename[:2], {})
    save_file(df_cities, save_dir_cities, filename, manual_alternate_names, clean_city)
    save_file(df_regions, save_dir_regions, filename, manual_alternate_names, clean_region)


def clean_punctuation(s: str) -> str:
    """
    Change exotic single quotes to regular single quote and remove any commas

    :param s: String to clean
    :return: Cleaned string
    """
    return s.replace("’", "'").replace("‘", "'").replace(",", "")


def is_latin(text: str) -> bool:
    """
    Identifies if a text is made up of latin characters or not

    :param text: Text to process
    :return: Boolean indicating whether it is completely latin
    """
    try:
        symbols_of_interest = {'HIEROGLYPH', 'IDEOGRAPH', 'LETTER', 'RADICAL', 'SYLLABLE', 'SYLLABICS'}
        character_names = (unicodedata.name(c) for c in text)
        return all('LATIN' in c for c in character_names if any(symbol in c for symbol in symbols_of_interest))
    except ValueError:
        # Character couldn't be found, definitely not LATIN
        return False


def add_alternate_names(work_dir: str, df_cities: pd.DataFrame, df_regions: pd.DataFrame,
                        filename: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the alternate names table and add alternative names to cities and regions

    :param work_dir: Working directory
    :param df_cities: DataFrame with cities
    :param df_regions: DataFrame with regions
    :param filename: Filename
    :return: Expanded cities and regions dataframes
    """
    # Load alternative names
    columns_alt = ['alternateNameId', 'geonameid', 'isolanguage', 'alternate name', 'isPreferredName', 'isShortName',
                   'isColloquial', 'isHistoric', 'from', 'to']
    df_alt = pd.read_csv(os.path.join(work_dir, 'alternatenames', filename), sep='\t', header=None,
                         names=columns_alt, keep_default_na=False)

    # Change exotic single quotes to regular single quote and remove any commas
    df_alt['alternate name'] = df_alt['alternate name'].apply(clean_punctuation)

    # Only retain useful and unique alternative names. Note that only the dominant languages up to English are taken
    # into account. This is a proxy for determining the domestic languages. We also take into account the rows without
    # known language (empty string) and the corresponding country code, as it has proven to be useful
    language_counts = df_alt.isolanguage.value_counts()
    threshold = language_counts.loc['en']
    dominant_languages = language_counts[language_counts >= threshold].index
    dominant_languages = {lang for lang in dominant_languages if len(lang) == 2}
    if len(dominant_languages) == 1:
        dominant_languages.add(filename[:2].lower())
    dominant_languages.update({'', 'abbr'})
    df_alt = df_alt[df_alt.isolanguage.isin(dominant_languages) & ~(df_alt.isColloquial == "1")]
    df_alt = df_alt.drop_duplicates(['geonameid', 'alternate name'], keep='first')
    df_alt = df_alt.drop(['alternateNameId', 'isolanguage', 'isPreferredName', 'isShortName', 'isColloquial',
                          'isHistoric', 'from', 'to'], axis=1)

    # Obtain unique lowercased original names. Alternate names cannot overlap the original ones
    original_names_cities = set(df_cities.name.apply(clean_city).to_list())
    original_names_regions = set(df_regions.name.apply(clean_city).to_list())
    df_alt_cities = df_alt[~df_alt['alternate name'].apply(clean_city).isin(original_names_cities)]
    df_alt_regions = df_alt[~df_alt['alternate name'].apply(clean_city).isin(original_names_regions)]

    # Group by ID, such that we have all the alternate names per main city/region in one row. This also sets geonameid
    # as index
    df_alt_cities = df_alt_cities.groupby(by='geonameid')['alternate name'].apply(set)
    df_alt_regions = df_alt_regions.groupby(by='geonameid')['alternate name'].apply(set)

    # Join and map NaN values to empty set for alternate names
    df_cities = df_cities.join(df_alt_cities, on='geonameid', how='left')
    df_regions = df_regions.join(df_alt_regions, on='geonameid', how='left')
    df_cities['alternate name'] = df_cities['alternate name'].apply(lambda x: set() if pd.isna(x) else x)
    df_regions['alternate name'] = df_regions['alternate name'].apply(lambda x: set() if pd.isna(x) else x)

    # Sometimes, city and region names overlap. In that case, we add the alternate names of the regions to the cities.
    # We only take into account administrative divisions
    df_cities['name_lower'] = df_cities.name.str.lower()
    df_regions['name_lower'] = df_regions.name.str.lower()
    df_regions_to_join = df_regions[df_regions['feature class'] == 'A']
    df_regions_to_join = df_regions_to_join.drop(['name', 'asciiname', 'feature class', 'feature code', 'geonameid'],
                                                 axis=1).set_index('name_lower')
    df_regions_to_join.columns = ['alternate region name']
    df_cities = df_cities.join(df_regions_to_join, on='name_lower', how='left')
    df_cities['alternate region name'] = df_cities['alternate region name'].apply(lambda x: set() if pd.isna(x) else x)
    if len(df_cities):
        df_cities['alternate name'] = df_cities.apply(lambda row: row['alternate name'] | row['alternate region name'],
                                                      axis=1)
    df_cities = df_cities.drop(['alternate region name'], axis=1)

    return df_cities, df_regions


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Removes duplicate entries based on name and asciiname, but taking the union of alternate names in the process.

    :param df: DataFrame of cities or regions
    :return: DataFrame of cities or regions
    """
    # Groupby name to get rid of duplicates. When rows are merged, we take the union of alternate names
    union_func = lambda x: reduce(set.union, x)
    df = df.groupby('name')[['asciiname', 'alternate name']].agg(
        {'alternate name': union_func, 'asciiname': 'first'}
    ).reset_index()

    # Combine names based on equal ascii name. Again, when rows are merged we take the union of alternate names
    df = df.groupby('asciiname')[['name', 'alternate name']].agg(
        {'name': lambda x: x.unique(), 'alternate name': union_func}
    ).reset_index()

    def process_multiple_names(row):
        """
        Does nothing if the name is already a string. However, in the other case where it's a list of strings we
        determine which variant has the most non-ascii characters and return that one. E.g., [Chenet, Chênet] -> Chênet.
        If there's a tie, we select the longest one. E.g. [Etten, Etten-Leur] -> Etten-Leur. If there's still a tie,
        sort and return the first one. The other name is added to the alternate names. If they are similar after `
        clean_city`, they will be removed when saving the names to file.
        """
        if isinstance(row['name'], str):
            return pd.Series([row['name'], row['alternate name']])
        names = sorted(((len(RE_ALPHA.sub('', name)), len(name), name) for name in row['name']),
                       key=lambda tup: (-tup[0], -tup[1], tup[2]))
        name = names[0][2]
        other_alternate_names = {name for _, _, name in names[1:]}
        return pd.Series([name, row['alternate name'] | other_alternate_names])

    # Choose the name with the most non-ascii characters. It doesn't really matter which one we choose, though. This
    # just looks prettier
    if len(df):
        df[['name', 'alternate name']] = df.apply(process_multiple_names, axis=1)

    # Drop columns that are no longer of interest and sort
    df = df.drop(['asciiname'], axis=1)
    df = df.sort_values('name')

    return df


def save_file(df: pd.DataFrame, save_dir: str, filename: str, manual_alternate_names: Dict[str, List[str]],
              clean_func: Callable) -> None:
    """
    Saves a dataframe to file

    :param df: DataFrame to save
    :param save_dir: Save directory
    :param filename: Filename
    :param manual_alternate_names: {city: list of manually added alternate names}
    :param clean_func: Clean function to use
    """
    # Store name + alternate names. The name and alternative names can have overlap, which we filter here
    with open(os.path.join(save_dir, filename), 'w') as f:
        for row in df.itertuples():
            name = row[1]
            names = row[1]
            skip_alternate_names = {clean_func(name)}
            alternate_names = []

            # Add alternate names
            if not pd.isna(row[2]):
                for alternate_name in sorted(row[2]):
                    cleaned_alternate_name = clean_func(alternate_name)
                    if cleaned_alternate_name not in skip_alternate_names:
                        alternate_names.append(alternate_name)
                        skip_alternate_names.add(cleaned_alternate_name)

            # Add manually added alternate names
            for alternate_name in manual_alternate_names.get(name, []):
                cleaned_alternate_name = clean_func(alternate_name)
                if cleaned_alternate_name not in skip_alternate_names:
                    alternate_names.append(alternate_name)
                    skip_alternate_names.add(cleaned_alternate_name)

            if alternate_names:
                names = f"{name}, {', '.join(sorted(alternate_names))}"

            f.write(f"{names}\n")


def main(geonames_dir: str, save_dir_cities: str, save_dir_regions: str) -> None:
    """
    Assumes the zip-files have been extracted

    :param geonames_dir: Geonames directory which should contain a file for each country, together with a folder called
        'alternatenames', which also contains a file for each country
    :param save_dir_cities: Save directory for cities
    :param save_dir_regions: Save directory for regions
    """
    # Locate all files with length 6: "<COUNTRY_CODE>.txt" (e.g., "NL.txt")
    filenames = os.listdir(geonames_dir)
    filenames = [filename for filename in filenames if len(filename) == 6]

    # Create save dirs
    os.makedirs(save_dir_cities, exist_ok=True)
    os.makedirs(save_dir_regions, exist_ok=True)

    # Add some manual ones
    manual_alternate_names = {'JP': {'Gifu-shi': ['Gifu']}}

    # Process files
    process_country_func = partial(process_country, work_dir=geonames_dir, save_dir_cities=save_dir_cities,
                                   save_dir_regions=save_dir_regions, manual_alternate_names=manual_alternate_names)
    if MPIRE_AVAILABLE:
        with WorkerPool(n_jobs=4) as pool:
            pool.map_unordered(process_country_func, filenames, chunk_size=1, progress_bar=True)
    else:
        for filename in tqdm(filenames):
            process_country_func(filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gd', type=str, help='Geonames directory', default='./')
    parser.add_argument('--sd-cities', type=str, help='Save directory for cities', default='./cities_per_country')
    parser.add_argument('--sd-regions', type=str, help='Save directory for regions', default='./regions_per_country')
    args = parser.parse_args()
    main(args.gd, args.sd_cities, args.sd_regions)
