
import os
import glob
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import snscrape.modules.twitter as sntwitter
import itertools
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

def get_page_covid_content(search):
    
    # Get temporary dataframe from collect
    df = pd.DataFrame(itertools.islice(sntwitter.TwitterSearchScraper(search).get_items(), None))
    if df.shape[0] == 0:
        return pd.DataFrame(), pd.DataFrame()
    df = df.rename(columns={'id':'tweetId'})
    users_df = pd.DataFrame(list(df.user.values))
    users_df = users_df.rename(columns={'id':'userId'})
    df['userId'] = users_df['userId']
    users_df = users_df.drop_duplicates('userId')
    users_df = users_df.drop('descriptionUrls', axis=1)
    df['longitude'] = df.coordinates.apply(lambda x: x['longitude'] if(np.all(pd.notnull(x))) else x)
    df['latitude'] = df.coordinates.apply(lambda x: x['latitude'] if(np.all(pd.notnull(x))) else x)
    df = df[[
        'tweetId', 'conversationId', 'userId', 'date', 'content', 'lang', 'sourceLabel',
        'replyCount', 'retweetCount', 'likeCount', 'quoteCount', 'longitude', 'latitude', 'place'
    ]]
    
    return df, users_df

def check_page(page):
    return os.path.exists('./data/raw/_tweets_tmp' + page + '.parquet')

def main():

    # Configurations
    logger = logging.getLogger(__name__)

    # Tweets schema
    tweets_fields = [
        pa.field('tweetId', pa.int64()),
        pa.field('conversationId', pa.int64()),
        pa.field('userId', pa.int64()),
        pa.field('date', pa.timestamp('ns', tz='UTC')),
        pa.field('content', pa.string()),
        pa.field('lang', pa.string()),
        pa.field('sourceLabel', pa.string()),
        pa.field('replyCount', pa.int32()),
        pa.field('retweetCount', pa.int32()),
        pa.field('likeCount', pa.int32()),
        pa.field('quoteCount', pa.int32()),
        pa.field('longitude', pa.float32()),
        pa.field('latitude', pa.float32()),
        pa.field('place', pa.string())
    ]
    tweets_schema = pa.schema(tweets_fields)

    # Tweets schema
    users_fields = [
        pa.field('username', pa.string()),
        pa.field('displayname', pa.string()),
        pa.field('userId', pa.int64()),
        pa.field('description', pa.string()),
        pa.field('rawDescription', pa.string()),
        pa.field('verified', pa.bool_()),
        pa.field('created', pa.timestamp('ns', tz='UTC')),
        pa.field('followersCount', pa.int32()),
        pa.field('friendsCount', pa.int32()),
        pa.field('statusesCount', pa.int32()),
        pa.field('favouritesCount', pa.int32()),
        pa.field('listedCount', pa.int32()),
        pa.field('mediaCount', pa.int32()),
        pa.field('location', pa.string()),
        pa.field('protected', pa.bool_()),
        pa.field('linkUrl', pa.string()),
        pa.field('linkTcourl', pa.string()),
        pa.field('profileImageUrl', pa.string()),
        pa.field('profileBannerUrl', pa.string())
    ]
    users_schema = pa.schema(users_fields)

    # Get search definitions
    since = '2020-01-01'
    until = '2021-04-30'
    keywords = pd.read_csv('./data/external/keywords.csv', header=None, names=['keywords']) 
    keywords = list(keywords.keywords.unique())
    news_accounts = pd.read_csv('./data/external/news_accounts_skynews.csv', sep=';')

    # Loop through news pages and get content
    logger.info('Start collecting tweets.')
    tpqwriter = tpqwriter = None
    keywords = ['wuhan', 'ncov', 'coronavirus', 'covid', 'sars-cov-2', 'pandemic', 'lockdown', 'quarantine', 
    'social distancing', 'wearing masks', 'vaccination', 'vaccine', 'outbreak', 'panic buying', 'remote working', 'homeschooling']
    for i, page in enumerate(news_accounts.account.values):
        search = "{} from:{} since:{} until:{}".format('''("''' + '''" OR "'''.join(keywords) + '''")''', page, since, until) 
        page_tweets, page_metadata = get_page_covid_content(search)
        if page_tweets.shape[0] == 0:
            print("Just finished", page)
            logger.info('Finish scrapping %s with %s rows.', page, str(page_tweets.shape[0]))
            continue
        page_tweets = pa.Table.from_pandas(page_tweets, schema=tweets_schema, preserve_index=False)
        page_metadata = pa.Table.from_pandas(page_metadata, schema=users_schema, preserve_index=False)
        if i == 0:
            # create a parquet write object giving it an output file
            tpqwriter = pq.ParquetWriter('./data/raw/tmp/news_tweets_skynews.parquet', tweets_schema, compression='gzip')
            upqwriter = pq.ParquetWriter('./data/raw/tmp/news_accounts_skynews.parquet', users_schema, compression='gzip')
        tpqwriter.write_table(page_tweets)
        upqwriter.write_table(page_metadata)
        print("Just finished", page)
        logger.info('Finish scrapping %s with %s rows.', page, str(page_tweets.shape[0]))

    # close the parquet writer
    if tpqwriter:
        tpqwriter.close()
    if upqwriter:
        upqwriter.close()

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logfile = './src/logs/' + datetime.now().strftime("%Y%m%d%H%M%S") + '_get_covid_tweet_news.log'
    logging.basicConfig(filename=logfile, level=logging.INFO, format=log_fmt, filemode='w')
    main()