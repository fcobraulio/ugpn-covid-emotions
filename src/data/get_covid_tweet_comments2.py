import random
import os
import glob
import logging
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
import snscrape.modules.twitter as sntwitter
import itertools
from time import sleep
import pyarrow as pa
import pyarrow.parquet as pq
from joblib import Parallel, delayed

def get_conversations():
    if os.path.isfile('./data/raw/_tmp_conversations.pickle'):
        return pd.read_pickle('./data/raw/_tmp_conversations.pickle')
    else:
        return pd.DataFrame({'conversationId': pd.Series([], dtype='int')})

def get_users():
    if os.path.isfile('./data/raw/_tmp_users.pickle'):
        return pd.read_pickle('./data/raw/_tmp_users.pickle')
    else:
        return pd.DataFrame({'userId': pd.Series([], dtype='int')})

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

def append_to_parquet_table(dataframe, schema, filepath=None, writer=None):
    """Method writes/append dataframes in parquet format.

    This method is used to write pandas DataFrame as pyarrow Table in parquet format. If the methods is invoked
    with writer, it appends dataframe to the already written pyarrow table.

    :param dataframe: pd.DataFrame to be written in parquet format.
    :param filepath: target file location for parquet file.
    :param writer: ParquetWriter object to write pyarrow tables in parquet format.
    :return: ParquetWriter object. This can be passed in the subsequenct method calls to append DataFrame
        in the pyarrow Table
    """
    table = pa.Table.from_pandas(dataframe, schema=schema, preserve_index=False)
    if writer is None:
        writer = pq.ParquetWriter(filepath, schema, compression='gzip')
    writer.write_table(table=table)
    return writer

def get_tweets_fields():
    return [
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

def get_users_fields():
    return [
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

def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))



def main():

    # Configurations
    logger = logging.getLogger(__name__)
    tweets_schema = pa.schema(get_tweets_fields())
    users_schema = pa.schema(get_users_fields()) 

    def simpleton_scrapper(batch):
        inner_break = False
        try:
            #sleep(random.randint(1,5))
            search = "conversation_id:" + " OR conversation_id:".join( [str(s) for s in batch]) + " lang:en"
            comments, users = get_page_covid_content(search)
            comments.to_parquet('./data/raw/tmp/comments/c_' + str(batch[0]) + '.parquet', index=False)
            users = users.drop_duplicates('userId')
            users.to_parquet('./data/raw/tmp/users/u_' + str(batch[0]) + '.parquet', index=False)
        except KeyboardInterrupt:
            inner_break = True
            logger.warning("Shutdown requested...exiting")
        except Exception:
            pass
            logger.exception('Problem with batch %d.', batch[0])
        return inner_break

    def wrapper_scrapper(batches):
        for batch in batches:
            inner_break = simpleton_scrapper(batch)
            if inner_break:
                break
        logger.warning('Finish scrapping batches %d.', batches[0][0])

    #
    # search_groups  = pickle.load(open('./data/external/search_groups3.sav', 'rb'))
    # group_codes = [c[0] for c in search_groups]
    # collected_codes = glob.glob('./data/raw/tmp/comments/*.parquet')
    # collected_codes = [x.strip('./data/raw/tmp/comments\\c_').strip('.parquet') for x in collected_codes]
    # remain_codes = np.setdiff1d(group_codes,collected_codes)
    # search_groups = [c for c in search_groups if c[0] in remain_codes]

    # Read 
    df = pd.read_parquet('./data/raw/tmp/news_tweets_skynews.parquet')
    df = df[df.replyCount>0]
    conversations = list(df.conversationId.unique())
    random.shuffle(conversations)
    search_groups = list(split(conversations, int(len(conversations)/12)))
    pickle.dump(search_groups, open('./data/external/search_groups6.sav', 'wb'))
    logger.warning('Starting conversations scrapping with %d conversations to be scrapped.', len(search_groups)*12)

    while len(search_groups) > 0:
        downloaded = [int(x[26:-8]) for x in glob.glob('./data/raw/tmp/comments/*.parquet')]
        search_groups = [batch for batch in search_groups if batch[0] not in downloaded]
        search_batches = list(split(search_groups, int(len(search_groups)/64)))
        logger.warning('There are still %d conversations to be scrapped.', len(search_groups)*12)
        Parallel(n_jobs=-1)(delayed(wrapper_scrapper)(batches) for batches in search_batches)

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logfile = './src/logs/' + datetime.now().strftime("%Y%m%d%H%M%S") + '_get_covid_tweet_comments.log'
    logging.basicConfig(filename=logfile, level=logging.WARNING, format=log_fmt, filemode='w')
    main()