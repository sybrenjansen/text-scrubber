# Geonames data downloaded from http://www.geonames.org/,
# Geonames is distributed under a Creative Commons Attribution 4.0 License:
# http://download.geonames.org/export/dump/readme.txt

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
                     usecols=['name', 'asciiname', 'feature class', 'feature code'], keep_default_na=False)

    # Only retain useful populated places
    df = df[(df['feature class'] == 'P') &
            ~(df['feature code'] == 'PPLCH') &
            ~(df['feature code'] == 'PPLH') &
            ~(df['feature code'] == 'PPLL') &
            ~(df['feature code'] == 'PPLQ') &
            ~(df['feature code'] == 'PPLR') &
            ~(df['feature code'] == 'PPLW') &
            ~(df['feature code'] == 'PPLX')]

    # Change ’ to '
    df['name'] = df['name'].apply(lambda s: s.replace("’", "'").replace("‘", "'"))

    # Drop columns used for filtering and duplicate entries, and sort
    df = df.drop_duplicates('asciiname', keep='first')
    df = df.drop_duplicates('name', keep='first')
    df = df.drop(['asciiname', 'feature class', 'feature code'], axis=1)
    df = df.sort_values('name')

    # Store
    with open(os.path.join(save_dir, filename), 'w') as f:
        for name in df.name.to_list():
            f.write(name + '\n')


def main(work_dir: str, save_dir: str):
    """
    Assumes the zip-files have been extracted

    :param work_dir: Working directory which should contain a file per each country
    :param save_dir: Save directory
    """
    # Locate all files with length 6: "<COUNTRY_CODE>.txt" (e.g., "NL.txt")
    filenames = os.listdir(work_dir)
    filenames = [filename for filename in filenames if len(filename) == 6]

    # Create save dir
    os.makedirs(save_dir, exist_ok=True)

    # Process files
    for filename in tqdm(filenames):
        process(work_dir, filename, save_dir)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--wd', type=str, help='Working directory', default='./')
    parser.add_argument('--sd', type=str, help='Save directory', default='./cities_per_country')
    args = parser.parse_args()
    main(args.wd, args.sd)
