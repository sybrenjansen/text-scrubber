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
from functools import reduce
from typing import Dict, List

import pandas as pd
from tqdm.auto import tqdm

from text_scrubber.geo import clean_city


def process(work_dir: str, filename: str, save_dir: str, manual_alternate_names: Dict[str, List[str]]) -> None:
    """
    :param work_dir: Working directory
    :param filename: Filename
    :param save_dir: Save directory
    :param manual_alternate_names: List of manually added alternate names
    """
    columns = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude', 'feature class',
               'feature code', 'country code', 'cc2', 'admin1 code', 'admin2 code', 'admin3 code', 'admin4 code',
               'population', 'elevation', 'dem', 'timezone', 'modification date']
    df = pd.read_csv(os.path.join(work_dir, filename), sep='\t', header=None, names=columns,
                     usecols=['geonameid', 'name', 'asciiname', 'feature class', 'feature code'], keep_default_na=False)

    # Load alternative names
    columns_alt = ['alternateNameId', 'geonameid', 'isolanguage', 'alternate name', 'isPreferredName', 'isShortName',
                   'isColloquial', 'isHistoric', 'from', 'to']
    df_alt = pd.read_csv(os.path.join(work_dir, 'alternatenames', filename), sep='\t', header=None,
                         names=columns_alt, keep_default_na=False)

    # Change ’ to '
    df['name'] = df['name'].apply(lambda s: s.replace("’", "'").replace("‘", "'"))
    df_alt['alternate name'] = df_alt['alternate name'].apply(lambda s: s.replace("’", "'").replace("‘", "'"))

    # Only retain useful and unique alternative names. Note that only the dominant languages up to English are taken
    # into account. This is a proxy for determining the domestic languages
    dominant_languages = [lang for lang, _ in sorted(df_alt.isolanguage.value_counts().items(),
                                                     key=lambda tup: -tup[1]) if len(lang) == 2]
    dominant_languages = dominant_languages[:dominant_languages.index('en') + 1]
    df_alt = df_alt[df_alt.isolanguage.isin(dominant_languages) & ~(df_alt.isColloquial == "1")]
    df_alt = df_alt.drop_duplicates(['geonameid', 'alternate name'], keep='first')
    df_alt = df_alt.drop(['alternateNameId', 'isolanguage', 'isPreferredName', 'isShortName', 'isColloquial',
                          'isHistoric', 'from', 'to'], axis=1)

    # Obtain unique lowercased original names. Alternate names cannot overlap the original ones. I know where doing
    # this filtering twice. Here, and later. But it makes it easier.
    original_names = set(df[(df['feature class'] == 'P') &
                            ~(df['feature code'] == 'PPLCH') &
                            ~(df['feature code'] == 'PPLH') &
                            ~(df['feature code'] == 'PPLL') &
                            ~(df['feature code'] == 'PPLQ') &
                            ~(df['feature code'] == 'PPLR') &
                            ~(df['feature code'] == 'PPLW') &
                            ~(df['feature code'] == 'PPLX')].name.apply(clean_city).to_list())
    df_alt = df_alt[~df_alt['alternate name'].apply(clean_city).isin(original_names)]

    # Group by ID, such that we have all the alternate names per main city in one row. This also sets geonameid as index
    df_alt = df_alt.groupby(by='geonameid')['alternate name'].apply(set)

    # Join and map NaN values to empty set for alternate names
    df = df.join(df_alt, on='geonameid', how='left')
    df['alternate name'] = df['alternate name'].apply(lambda x: set() if pd.isna(x) else x)

    # Obtain administrative divisions. Sometimes, there are divisions that match name with a populated place. Those
    # divisions can have alternate names that are useful for those populated places as well. So, we'll try to match them
    # on name and combine the geoname_ids
    df_adm_div = df[df['feature code'].isin({'ADM1', 'ADM2', 'ADM3', 'ADM4', 'ADM5'})]

    # Only retain useful populated places
    df = df[(df['feature class'] == 'P') &
            ~(df['feature code'] == 'PPLCH') &
            ~(df['feature code'] == 'PPLH') &
            ~(df['feature code'] == 'PPLL') &
            ~(df['feature code'] == 'PPLQ') &
            ~(df['feature code'] == 'PPLR') &
            ~(df['feature code'] == 'PPLW') &
            ~(df['feature code'] == 'PPLX')]

    # Groupby name to get rid of duplicates. Now we are left with unique names, but they can have multiple geonameids
    # and alternate names
    union_func = lambda x: reduce(set.union, x)
    df = df.groupby('name')[['geonameid', 'asciiname', 'alternate name']].agg(
        {'alternate name': union_func, 'asciiname': 'first'}
    ).reset_index()

    # Match administrative divisions to populated places and add their geoname_ids
    df_adm_div['name_lower'] = df_adm_div.name.str.lower()
    df_adm_div = df_adm_div.drop(['name', 'asciiname', 'geonameid', 'feature class', 'feature code'], axis=1)
    df_adm_div = df_adm_div.set_index('name_lower')
    df_adm_div.columns = ['alternate name_alt']
    df['name_lower'] = df.name.str.lower()
    df = df.join(df_adm_div, on='name_lower', how='left')
    df['alternate name_alt'] = df['alternate name_alt'].apply(lambda x: set() if pd.isna(x) else x)
    if len(df):
        df['alternate name'] = df.apply(lambda row_: row_['alternate name'] | row_['alternate name_alt'], axis=1)

    # Combine names based on equal ascii name
    df = df.groupby('asciiname')[['name', 'alternate name']].agg({'name': 'first',
                                                                  'alternate name': union_func}).reset_index()

    # Drop columns that are no longer of interest and sort
    df = df.drop(['asciiname'], axis=1)
    df = df.sort_values('name')

    # Store name + alternate names. The name and alternative names can have overlap
    with open(os.path.join(save_dir, filename), 'w') as f:
        for row in df.itertuples():
            name = row[1]
            names = row[1]
            skip_alternate_names = set()
            alternate_names = []

            # Add alternate names
            if not pd.isna(row[2]):
                for alternate_name in row[2]:
                    cleaned_alternate_name = clean_city(alternate_name)
                    if cleaned_alternate_name not in skip_alternate_names:
                        alternate_names.append(alternate_name)
                        skip_alternate_names.add(cleaned_alternate_name)

            # Add manually added alternate names
            for alternate_name in manual_alternate_names.get(name, []):
                cleaned_alternate_name = clean_city(alternate_name)
                if cleaned_alternate_name not in skip_alternate_names:
                    alternate_names.append(alternate_name)
                    skip_alternate_names.add(cleaned_alternate_name)

            if alternate_names:
                names = f"{name}, {', '.join(sorted(alternate_names))}"

            f.write(f"{names}\n")


def main(geonames_dir: str, save_dir: str):
    """
    Assumes the zip-files have been extracted

    :param geonames_dir: Geonames directory which should contain a file for each country, together with a folder called
        'alternatenames', which also contains a file for each country
    :param save_dir: Save directory
    """
    # Locate all files with length 6: "<COUNTRY_CODE>.txt" (e.g., "NL.txt")
    filenames = os.listdir(geonames_dir)
    filenames = [filename for filename in filenames if len(filename) == 6]

    # Create save dir
    os.makedirs(save_dir, exist_ok=True)

    # Add some manual ones
    manual_alternate_names = {'JP': {'Gifu-shi': ['Gifu']}}

    # Process files
    for filename in tqdm(filenames):
        process(geonames_dir, filename, save_dir, manual_alternate_names.get(filename[:2], {}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gd', type=str, help='Geonames directory', default='./')
    parser.add_argument('--sd', type=str, help='Save directory', default='./cities_per_country')
    args = parser.parse_args()
    main(args.gd, args.sd)
