
import sys
sys.path.append('./../../')

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
import snscrape.modules.twitter as sntwitter
import itertools
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

    # Get already collected conversations and users
    conversations = get_conversations()
    users = get_users()

    # Get temporary dataframe from collect
    df = pd.DataFrame(itertools.islice(sntwitter.TwitterSearchScraper(search).get_items(), None))
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

    # Update users and conversations frames
    users_df = users_df[~(users_df.userId.isin(users.userId.values))]
    users = pd.concat([users, pd.DataFrame(users_df.userId)])
    conversations = pd.concat([conversations, pd.DataFrame(df.conversationId)])
    users.to_pickle('./data/raw/_tmp_users.pickle')
    conversations.to_pickle('./data/raw/_tmp_conversations.pickle')

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

def main():

    # Configurations
    logger = logging.getLogger(__name__)
    tweets_schema = pa.schema(get_tweets_fields())
    users_schema = pa.schema(get_users_fields())
    conversations = get_conversations()

    # Read news tweets
    news_tweets = pd.read_parquet('./data/raw/tmp/news_tweets_skynews.parquet')
    page_metadata = pd.read_parquet('./data/raw/tmp/news_accounts_skynews.parquet')

    # Define list of conversations yet to be collected
    news_tweets = news_tweets[
        ~(news_tweets.conversationId.isin(conversations.conversationId.values)) &
        (news_tweets.replyCount>0)
    ]

    # Define page lookup
    page_lookup = {userId:username for userId,username in zip(page_metadata['userId'], page_metadata['username'])}

    # Loop through news pages and get content
    logger.warning('Start collecting tweets.')
    tpqwriter = upqwriter = None
    inner_break = False
    for name, group in news_tweets.groupby('userId'):
        group = group.reset_index(drop=True)
        logger.warning('Start scrapping %s with %d conversations with %d replies.', 
            page_lookup[name], len(group.conversationId.unique()), group.replyCount.sum())
        for lower in range(0, len(group.conversationId.unique()), 12):
            upper = min(lower + 12, len(group.conversationId.unique()))
            search = "conversation_id:" + " OR conversation_id:".join(
                [str(s) for s in list(group.conversationId[lower:upper].values)]
            ) + " lang:en"
            try:
                page_comments, user_metadata = get_page_covid_content(search)
                tpqwriter = append_to_parquet_table(page_comments, tweets_schema, './data/raw/tmp/news_comments_skynews.parquet', tpqwriter)
                upqwriter = append_to_parquet_table(user_metadata, users_schema, './data/raw/tmp/news_users_skynews.parquet', upqwriter)
                logger.warning('Collected %d replies from %s conversations ranging from %d to %d, still %s to collect.', 
                    page_comments.shape[0], page_lookup[name], lower, upper, (len(group.conversationId.unique())-upper))
            except KeyboardInterrupt:
                logger.warning("Shutdown requested...exiting")
                inner_break = True
                break
            except Exception:
                logger.exception('Problem with %s in execution #%d.', page_lookup[name], lower)
                pass
        if inner_break:
            break
        logger.warning('Finish scrapping %s with %s rows.', page_lookup[name], str(page_comments.shape[0]))

    # close the parquet writer
    tpqwriter.close(); upqwriter.close()

if __name__ == '__main__':
    log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logfile = './src/logs/' + datetime.now().strftime("%Y%m%d%H%M%S") + '_get_covid_tweet_comments.log'
    logging.basicConfig(filename=logfile, level=logging.WARNING, format=log_fmt, filemode='w')
    main()