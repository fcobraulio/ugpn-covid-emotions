
import os
#from src.helper.custom_funcs import get_page_covid_content
import glob
import logging
import pandas as pd
import numpy as np
from datetime import timedelta
import snscrape.modules.twitter as sntwitter
import itertools
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

def get_page_covid_content(search):
    
    # Get temporary dataframe from collect
    df = pd.DataFrame(itertools.islice(sntwitter.TwitterSearchScraper(search).get_items(), 100))
    df = df.rename(columns={'id':'tweetId'})
    users_df = pd.DataFrame(list(df.user.values))
    users_df = users_df.rename(columns={'id':'userId'})
    df['userId'] = users_df['userId']
    users_df = users_df.drop_duplicates('userId')
    df = df[[
        'tweetId', 'conversationId', 'userId', 'date', 'content', 'lang', 'sourceLabel', 
        'replyCount', 'retweetCount', 'likeCount', 'quoteCount', 'coordinates', 'place'
    ]]
    
    return df, users_df

def check_page(page):
    return os.path.exists('./data/raw/' + page + '.parquet')

def main():

    # Configurations
    logger = logging.getLogger(__name__)

    # Get accounts
    news_accounts = pd.read_parquet('./data/raw/news_accounts.parquet')[:5]

    # Constants
    since = '2020-01-01'
    until = '2021-04-30'
    keywords = '(wuhan OR ncov OR coronavirus OR covid OR sars-cov-2 OR pandemic)'

    # Loop through news pages and get content
    logger.info('Start collecting tweets.')
    for page in news_accounts.username.values:
        if check_page(page):
            continue
        search = "{} from:{} since:{} until:{}".format(keywords, page, since, until)
        page_tweets, page_metadata = get_page_covid_content(search)
        page_tweets.to_parquet('./data/raw/tweets_tmp/' + page + '.parquet')
        page_metadata.to_parquet('./data/raw/users_tmp/' + page + '.parquet')
        logger.info('Finish scrapping %s with %s rows.', page, str(page_tweets.shape[0]))

    # Consolidate data
    # files = glob.glob('./data/raw/tmp/*.parquet')
    # for file in files:

    # pq.write_table(pa.concat_tables(content), './data/raw/covid_tweet_news.parquet', compression='gzip')
    # pd.DataFrame(users).to_parquet('./data/raw/covid_account_news.parquet', compression='gzip')

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logfile = './src/logs/get_covid_tweet_news.log'
    logging.basicConfig(filename=logfile, level=logging.INFO, format=log_fmt, filemode='w')
    main()