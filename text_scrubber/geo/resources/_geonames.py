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
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Set

import pandas as pd
from tqdm.auto import tqdm

from text_scrubber.geo import clean_city, clean_region
from _geonames_overrides import MANUAL_ALTERNATE_NAMES_CITY, MANUAL_ALTERNATE_NAMES_REGION, MANUAL_HIERARCHY

try:
    from mpire import WorkerPool
    MPIRE_AVAILABLE = True
except ImportError:
    WorkerPool = None
    MPIRE_AVAILABLE = False

RE_NON_ASCII = re.compile(r"[a-zA-Z0-9() ]")
RE_JUNK = re.compile(r"[0-9()]")


def main(geonames_dir: str, save_dir_cities: str, save_dir_regions: str, countries: List[str]) -> None:
    """
    Assumes the zip-files have been extracted

    :param geonames_dir: Geonames directory which should contain a file for each country, together with a folder called
        'alternatenames', which also contains a file for each country
    :param save_dir_cities: Save directory for cities
    :param save_dir_regions: Save directory for regions
    :param countries: Countries to process
    """
    # Locate all files with length 6: "<COUNTRY_CODE>.txt" (e.g., "NL.txt")
    filenames = os.listdir(geonames_dir)
    filenames = [filename for filename in filenames if len(filename) == 6]
    countries = {country.upper() for country in countries}
    if 'ALL' not in countries:
        filenames = [filename for filename in filenames if filename[:2] in countries]

    # Load languages and hierarchy
    country_langs_map = load_languages(geonames_dir)
    df_hierarchy = load_hierarchy(geonames_dir)

    # Create save dirs
    os.makedirs(save_dir_cities, exist_ok=True)
    os.makedirs(save_dir_regions, exist_ok=True)

    # Process files
    process_country_func = partial(process_country, geonames_dir=geonames_dir, save_dir_cities=save_dir_cities,
                                   save_dir_regions=save_dir_regions, country_langs_map=country_langs_map,
                                   df_hierarchy=df_hierarchy, manual_hierarchy=MANUAL_HIERARCHY,
                                   manual_alternate_names_city=MANUAL_ALTERNATE_NAMES_CITY,
                                   manual_alternate_names_region=MANUAL_ALTERNATE_NAMES_REGION)
    if MPIRE_AVAILABLE:
        with WorkerPool(n_jobs=4) as pool:
            pool.map_unordered(process_country_func, filenames, chunk_size=1, progress_bar=True)
    else:
        for filename in tqdm(filenames):
            process_country_func(filename)


def load_languages(geonames_dir: str) -> Dict[str, Set[str]]:
    """
    Loads languages per country

    :param geonames_dir: Geonames directory
    :return: {country code: set of languages} dictionary
    """
    columns = ['ISO', 'ISO3', 'ISO-Numeric', 'fips', 'Country', 'Capital', 'Area(in sq km)', 'Population', 'Continent',
               'tld', 'CurrencyCode', 'CurrencyName', 'Phone', 'Postal Code Format', 'Postal Code Regex', 'Languages',
               'geonameid', 'neighbours', 'EquivalentFipsCode']
    df = pd.read_csv(os.path.join(geonames_dir, 'countryInfo.txt'), sep='\t', header=None, names=columns, skiprows=51,
                     usecols=['ISO', 'Languages']).set_index('ISO')
    df = df[~pd.isna(df.index)]

    # Parse languages and only retain two-letter codes
    df['Languages'] = df['Languages'].apply(lambda langs: set() if pd.isna(langs) else
                                            {lang.split('-')[0] for lang in langs.split(',')})
    df['Languages'] = df['Languages'].apply(lambda langs: {lang for lang in langs if len(lang) == 2})

    return df.to_dict()['Languages']


def load_hierarchy(geonames_dir: str) -> pd.DataFrame:
    """
    Load hierarchy file. Remove relationships that aren't ADM, other types can contain some noise. Some children have
    multiple parents, so group them to one row

    :param geonames_dir: Geonames directory
    :return: DataFrame containing child and parent IDs
    """
    df = pd.read_csv(os.path.join(geonames_dir, 'hierarchy.txt'), sep='\t', header=None,
                     names=['parentid', 'childid', 'type'])
    df = df[df.type == 'ADM'].drop(['type'], axis=1)
    df.parentid = df.parentid.apply(lambda pid: {pid})
    df = df.groupby('childid').agg({'parentid': set_union})

    return df


def set_union(s: Iterable[Set]) -> Set:
    """
    Returns the union of the list of sets

    :param s: List of sets
    :return: Union of list of sets
    """
    return reduce(set.union, s)


def process_country(filename: str, geonames_dir: str, save_dir_cities: str, save_dir_regions: str,
                    country_langs_map: Dict[str, Set[str]], df_hierarchy: pd.DataFrame,
                    manual_hierarchy: Dict[str, Dict[str, List[str]]],
                    manual_alternate_names_city: Dict[str, Dict[str, List[str]]],
                    manual_alternate_names_region: Dict[str, Dict[str, List[str]]]) -> None:
    """
    Processes a single country file and stores the results to file, one for cities, one for regions.

    :param filename: Filename
    :param geonames_dir: Geonames directory
    :param save_dir_cities: Save directory for cities
    :param save_dir_regions: Save directory for regions
    :param country_langs_map: {country code: set of languages} dictionary
    :param df_hierarchy: Pandas DataFrame containing hierarchy information of cities
    :param manual_hierarchy: {country code: {parent city name: list of children city names to merge}}
    :param manual_alternate_names_city: {country code: {city: list of manually added alternate names}}
    :param manual_alternate_names_region: {country code: {region: list of manually added alternate names}}
    """
    columns = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude', 'feature class',
               'feature code', 'country code', 'cc2', 'admin1 code', 'admin2 code', 'admin3 code', 'admin4 code',
               'population', 'elevation', 'dem', 'timezone', 'modification date']
    df = pd.read_csv(os.path.join(geonames_dir, filename), sep='\t', header=None, names=columns,
                     usecols=['geonameid', 'name', 'asciiname', 'feature class', 'feature code', 'population'],
                     keep_default_na=False)

    # Change exotic single quotes to regular single quote and remove any commas
    df['name'] = df['name'].apply(clean_punctuation)

    # Replace name by asciiname when it's not in Latin alphabet. We keep the alternate names in non-Latin, that's fine
    df['name'] = df[['name', 'asciiname']].apply(
        lambda row_: row_['name'] if is_latin(row_['name']) else row_['asciiname'], axis=1
    )

    # Only retain useful populated places for cities
    populated_places = {'PPL', 'PPLA', 'PPLA2', 'PPLA3', 'PPLA4', 'PPLA5', 'PPLC', 'PPLF', 'PPLG', 'PPLS'}
    df_cities = df[df['feature code'].isin(populated_places)]

    # Obtain regions. A=country, state, region,...; H=stream, lake, ...; L=parks, area, ...;
    # T=mountain, hill, rock, ...; V=forest, heath, ..., PPLL=populated locality; PPLX: section of populated place
    df_regions = df[df['feature class'].isin({'A', 'H', 'L', 'T', 'V'}) |
                    df['feature code'].isin({'PPLL', 'PPLX'})]

    # Add alternate names for cities and regions
    df_cities, df_regions = add_alternate_names(geonames_dir, df_cities, df_regions, country_langs_map, filename)

    # Merge children neighborhoods with parent cities
    manual_hierarchy = manual_hierarchy.get(filename[:2], {})
    df_cities = merge_on_hierarchy(df_cities, df_hierarchy, manual_hierarchy)

    # Remove duplicate names and drop columns that are no longer of interest
    df_cities, dropped_cities = remove_duplicates_and_without_population(df_cities, clean_city,
                                                                         drop_population=True, drop_columns=True)
    df_regions, _ = remove_duplicates_and_without_population(df_regions, clean_region,
                                                             drop_population=False, drop_columns=False)

    # Merge cities without population with regions
    df_regions = pd.concat([df_regions, dropped_cities])
    df_regions, _ = remove_duplicates_and_without_population(df_regions, clean_region,
                                                             drop_population=False, drop_columns=True)

    # Save to file
    manual_alternate_names_city = manual_alternate_names_city.get(filename[:2], {})
    manual_alternate_names_region = manual_alternate_names_region.get(filename[:2], {})
    save_file(df_cities, save_dir_cities, filename, manual_alternate_names_city, clean_city)
    save_file(df_regions, save_dir_regions, filename, manual_alternate_names_region, clean_region)


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


def add_alternate_names(geonames_dir: str, df_cities: pd.DataFrame, df_regions: pd.DataFrame,
                        country_langs_map: Dict[str, Set[str]], filename: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the alternate names table and add alternative names to cities and regions

    :param geonames_dir: Geonames directory
    :param df_cities: DataFrame with cities
    :param df_regions: DataFrame with regions
    :param country_langs_map: {country code: set of languages} dictionary
    :param filename: Filename
    :return: Expanded cities and regions dataframes
    """
    # Load alternative names
    columns_alt = ['alternateNameId', 'geonameid', 'isolanguage', 'alternate name', 'isPreferredName', 'isShortName',
                   'isColloquial', 'isHistoric', 'from', 'to']
    df_alt = pd.read_csv(os.path.join(geonames_dir, 'alternatenames', filename), sep='\t', header=None,
                         names=columns_alt, keep_default_na=False)

    # Change exotic single quotes to regular single quote and remove any commas
    df_alt['alternate name'] = df_alt['alternate name'].apply(clean_punctuation)

    # Only retain useful and unique alternative names. Note that, apart from the languages spoken in a country, the
    # dominant languages up to English are taken into account. We also take into account the rows without known language
    language_counts = df_alt.isolanguage.value_counts()
    threshold = language_counts.loc['en']
    dominant_languages = language_counts[language_counts >= threshold].index
    dominant_languages = {lang for lang in dominant_languages if len(lang) == 2}
    dominant_languages.update({'', 'abbr'})
    dominant_languages.update(country_langs_map.get(filename[:2], set()))
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
    df_regions_to_join = df_regions_to_join.drop(['name', 'asciiname', 'feature class', 'feature code', 'geonameid',
                                                  'population'], axis=1).set_index('name_lower')
    df_regions_to_join.columns = ['alternate region name']
    df_regions_to_join = df_regions_to_join[df_regions_to_join['alternate region name'].apply(len) > 0]
    df_regions_to_join = df_regions_to_join.groupby('name_lower').agg({'alternate region name': set_union})
    df_cities = df_cities.join(df_regions_to_join, on='name_lower', how='left')
    df_cities['alternate region name'] = df_cities['alternate region name'].apply(lambda x: set() if pd.isna(x) else x)
    if len(df_cities):
        df_cities['alternate name'] = df_cities.apply(lambda row: row['alternate name'] | row['alternate region name'],
                                                      axis=1)
    df_cities = df_cities.drop(['alternate region name'], axis=1)

    return df_cities, df_regions


def merge_on_hierarchy(df: pd.DataFrame, df_hierarchy: pd.DataFrame,
                       manual_hierarchy: Dict[str, List[str]]) -> pd.DataFrame:
    """
    Merges children cities with their parents. I.e., when a populated place is a neighborhood, the name and alternate
    names of that neighborhood will be added to the parent city. E.g., 'Manhatten' -> 'New York City'.

    :param df: Original DataFrame of cities
    :param df_hierarchy: Hierarchy DataFrame containing child and parent IDs
    :param manual_hierarchy: {parent city name: list of children city names to merge}
    :return: DataFrame where children have been merged with their parents
    """
    # Obtain parent IDs
    df['parentid'] = [{} for _ in range(len(df))]
    in_hierarchy_mask = df['geonameid'].isin(df_hierarchy.index)
    df.loc[in_hierarchy_mask, 'parentid'] = df_hierarchy.loc[df.loc[in_hierarchy_mask, 'geonameid'],
                                                             'parentid'].to_list()

    # Add manual parent IDs
    for parent_name, children_names in manual_hierarchy.items():
        parent_id = df[df['name'] == parent_name].iloc[0].geonameid
        children_mask = df['name'].isin(children_names)
        df.loc[children_mask, 'parentid'] = [{parent_id} for _ in range(sum(children_mask))]

    # Remove parent IDs that do not occur in this set
    city_geonameids = set(df['geonameid'].to_list())
    df['parentid'] = df['parentid'].apply(lambda pids: {pid for pid in pids if pid in city_geonameids})

    # Remove entries where there are multiple parent IDs. At this point, this shouldn't really occur anymore, but to
    # be safe. In the case there is a single parent ID, we merge it with the parent. Note, that we iteratively merge,
    # as there can be multiple consecutive parent relationships. E.g., A has to be merged with B, and B with C. In that
    # case the names of B can first be added to C, and then A with B. That means the names of A haven't been merged yet
    # with C, so we sweep over it a second time, third time ... until there are no more changes. This process can
    # probably be done more efficiently, but it doesn't really matter as there aren't that many merges happening.
    df = df.set_index('geonameid')
    in_hierarchy_mask = df['parentid'].apply(len) == 1
    has_changed = True
    while has_changed:
        has_changed = False
        for _, row in df[in_hierarchy_mask].iterrows():
            parent_id = next(iter(row['parentid']))
            prev_n_alternate_names = len(df.loc[parent_id, 'alternate name'])
            df.loc[parent_id, 'alternate name'].update(row['alternate name'] | {row['name']})
            df.loc[parent_id, 'population'] = max(df.loc[parent_id, 'population'], row['population'])
            if len(df.loc[parent_id, 'alternate name']) != prev_n_alternate_names:
                has_changed = True

    # Get rid of the children
    df = df[~in_hierarchy_mask]

    return df


def remove_duplicates_and_without_population(df: pd.DataFrame, clean_func: Callable, drop_population: bool,
                                             drop_columns: bool) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Removes duplicate entries based on name and asciiname, but taking the union of alternate names in the process. Also
    removes any alternate name that equals a city name. E.g., Austin as neighborhood of Chicago is removed as alternate
    name of Chicago, as it is also a city. Entries without population are also removed.

    :param df: DataFrame of cities or regions
    :param clean_func: Clean function to use
    :param drop_population: Whether to drop entries without population
    :param drop_columns: Whether to drop unused columns
    :return: DataFrame of cities or regions
    """
    # Groupby name to get rid of duplicates. When rows are merged, we take the union of alternate names
    df['cleaned_name'] = df['name'].apply(clean_func)
    df['name'] = df['name'].apply(lambda name: {name})
    df = df.groupby('cleaned_name')[['asciiname', 'alternate name', 'name', 'population']].agg(
        {'name': set_union, 'alternate name': set_union, 'asciiname': 'first', 'population': max}
    ).reset_index()

    # Combine names based on equal ascii name. Again, when rows are merged we take the union of alternate names
    df = df.groupby('asciiname')[['name', 'alternate name', 'population']].agg(
        {'name': set_union, 'alternate name': set_union, 'population': max}
    ).reset_index()

    def process_multiple_names(row):
        """
        Does nothing if the name is already a string. However, in the other case where it's a list of strings we
        determine which variant has the most non-ascii characters and return that one. E.g., [Chenet, Chênet] -> Chênet.
        We penalize heavily here on names that use numbers and parentheses. E.g. [Agrovila, Agrovila 2] -> Agrovila.
        If there's a tie, we select the longest one. E.g. [Etten, Etten-Leur] -> Etten-Leur. If there's still a tie,
        sort and return the first one. The other name is added to the alternate names. If they are similar after `
        clean_city`, they will be removed when saving the names to file.
        """
        if isinstance(row['name'], str):
            return pd.Series([row['name'], row['alternate name']])
        names = sorted(((len(RE_NON_ASCII.sub('', name).strip(' -')) - len(RE_JUNK.findall(name)) * 2, len(name), name)
                        for name in row['name']), key=lambda tup: (-tup[0], -tup[1], tup[2]))
        name = names[0][2]
        other_alternate_names = {name for _, _, name in names[1:]}
        return pd.Series([name, row['alternate name'] | other_alternate_names])

    # Choose the name with the most non-ascii characters. It doesn't really matter which one we choose, though. This
    # just looks prettier
    if len(df):
        df[['name', 'alternate name']] = df.apply(process_multiple_names, axis=1)

    # Remove cities and regions without population
    if drop_population:
        dropped = df[df['population'] == 0]
        df = df[df['population'] > 0].drop(['population'], axis=1)
    else:
        dropped = None

    # Remove alternate names that are also already names
    unique_names = set(df.name.to_list())
    df['alternate name'] = df['alternate name'].apply(lambda names: names - unique_names)

    # Drop columns that are no longer of interest and sort
    if drop_columns:
        df = df.drop(['asciiname'], axis=1)
    df = df.sort_values('name')

    return df, dropped


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gd', type=str, help='Geonames directory', default='./')
    parser.add_argument('--sd-cities', type=str, help='Save directory for cities', default='./cities_per_country')
    parser.add_argument('--sd-regions', type=str, help='Save directory for regions', default='./regions_per_country')
    parser.add_argument('--countries', type=str, help='List of two-letter country codes to process. Default=all',
                        nargs="*", default=['all'])
    args = parser.parse_args()
    main(args.gd, args.sd_cities, args.sd_regions, args.countries)
