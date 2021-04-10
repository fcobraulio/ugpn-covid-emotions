# Description: this script converts a raw external file describing US cities 2019 population estimation
# and casts to processed format.

# Source: https://www2.census.gov/programs-surveys/popest/tables/2010-2019/cities/totals/SUB-IP-EST2019-ANNRNK.xlsx*
# Annual Estimates of the Resident Population for Incorporated Places of 50,000 or More, 
# Ranked by July 1, 2019 Population: April 1, 2010 to July 1, 2019
# * original file was transformed in Excel to make it readable to python.

# -*- coding: utf-8 -*-
import click
import logging
from pathlib import Path
from dotenv import find_dotenv, load_dotenv
import pandas as pd


@click.command()
@click.argument('input_filepath', type=click.Path(exists=True))
@click.argument('output_filepath', type=click.Path())
def main(input_filepath, output_filepath):
    """ Runs data processing scripts to turn raw data from (../raw) into
        cleaned data ready to be analyzed (saved in ../processed).
    """
    logger = logging.getLogger(__name__)
    logger.info('making final data set from raw data')
    df = pd.read_csv(input_filepath, sep=';')
    df['Population'] = df['2019'].apply(lambda x: x.replace('.','')).astype(int)
    df['State'] = df.State.apply(lambda x: x.strip())
    df = pd.concat([df[df.Population>200000], df.groupby('State').head(3)]).drop_duplicates()
    df = df[['Rank', 'City', 'State', 'Population']]
    df = df[df.Population>50000].reset_index(drop=True)
    df['loctag'] = df.apply(lambda x: x.City.replace(' city', '') + ", " + x.State, axis=1)
    df.to_csv(output_filepath)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_fmt)

    # not used in this stub but often useful for finding various files
    project_dir = Path(__file__).resolve().parents[2]

    # find .env automagically by walking up directories until it's found, then
    # load up the .env entries as environment variables
    load_dotenv(find_dotenv())

    main()
