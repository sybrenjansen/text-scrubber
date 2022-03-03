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

import pandas as pd
from tqdm.auto import tqdm


def process(work_dir: str, filename: str, save_dir: str) -> None:
    """
    :param work_dir: Working directory
    :param filename: Filename
    :param save_dir: Save directory
    """
    columns = ['geonameid', 'name', 'asciiname', 'alternatenames', 'latitude', 'longitude', 'feature class',
               'feature code', 'country code', 'cc2', 'admin1 code', 'admin2 code', 'admin3 code', 'admin4 code',
               'population', 'elevation', 'dem', 'timezone', 'modification date']
    df = pd.read_csv(os.path.join(work_dir, filename), sep='\t', header=None, names=columns,
                     usecols=['geonameid', 'name', 'asciiname', 'feature class', 'feature code'], keep_default_na=False)

    # Only retain useful populated places
    df = df[(df['feature class'] == 'P') &
            ~(df['feature code'] == 'PPLCH') &
            ~(df['feature code'] == 'PPLH') &
            ~(df['feature code'] == 'PPLL') &
            ~(df['feature code'] == 'PPLQ') &
            ~(df['feature code'] == 'PPLR') &
            ~(df['feature code'] == 'PPLW') &
            ~(df['feature code'] == 'PPLX')]

    # Load alternative names
    columns_alt = ['alternateNameId', 'geonameid', 'isolanguage', 'alternate name', 'isPreferredName', 'isShortName',
                   'isColloquial', 'isHistoric', 'from', 'to']
    df_alt = pd.read_csv(os.path.join(work_dir, 'alternatenames', filename), sep='\t', header=None,
                         names=columns_alt, keep_default_na=False)

    # Only retain useful and unique alternative names. Note that only the dominant languages up to English are taken
    # into account. This is a proxy for determining the domestic languages
    dominant_languages = [lang for lang, _ in sorted(df_alt.isolanguage.value_counts().items(),
                                                     key=lambda tup: -tup[1]) if len(lang) == 2]
    dominant_languages = dominant_languages[:dominant_languages.index('en') + 1]
    df_alt = df_alt[((df_alt.isPreferredName == "1") | (df_alt.isShortName == "1") | (df_alt.isHistoric == "1")) &
                    df_alt.isolanguage.isin(dominant_languages) &
                    ~(df_alt.isColloquial == "1")]
    df_alt = df_alt.drop_duplicates(['geonameid', 'alternate name'], keep='first')
    df_alt = df_alt.drop(['alternateNameId', 'isolanguage', 'isPreferredName', 'isShortName', 'isColloquial',
                          'isHistoric', 'from', 'to'], axis=1)

    # Change ’ to '
    df['name'] = df['name'].apply(lambda s: s.replace("’", "'").replace("‘", "'"))
    df_alt['alternate name'] = df_alt['alternate name'].apply(lambda s: s.replace("’", "'").replace("‘", "'"))

    # Group by ID, such that we have all the alternate names per main city in one row. This also sets geonameid as index
    df_alt = df_alt.groupby(by='geonameid')['alternate name'].apply(set)

    # Drop columns used for filtering and duplicate entries, and sort
    df = df.drop_duplicates('asciiname', keep='first')
    df = df.drop_duplicates('name', keep='first')
    df = df.drop(['asciiname', 'feature class', 'feature code'], axis=1)
    df = df.sort_values('name')

    # Match cities with alternative names
    df = df.set_index('geonameid')
    df_joined = df.join(df_alt, how='left')

    # Store name + alternate names. The name and alternative names can have overlap
    with open(os.path.join(save_dir, filename), 'w') as f:
        for row in df_joined.itertuples():
            names = row[1]
            if not pd.isna(row[2]):
                name = row[1]
                alternate_names = row[2] - {name}
                if alternate_names:
                    names = f"{name}, {', '.join(alternate_names)}"
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

    # Process files
    for filename in tqdm(filenames):
        process(geonames_dir, filename, save_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--gd', type=str, help='Geonames directory', default='./')
    parser.add_argument('--sd', type=str, help='Save directory', default='./cities_per_country')
    args = parser.parse_args()
    main(args.gd, args.sd)
