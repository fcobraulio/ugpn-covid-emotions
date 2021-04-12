import glob
import pandas as pd

def render_df(file):

    # Read Data
    df = pd.read_parquet(file)
    users_df = pd.DataFrame(list(df.user.values))
    df['userId'] = users_df.id

    # Clear Comments DataFrame
    df = df[[
        'id', 'conversationId', 'userId', 'date', 'content', 'lang', 'sourceLabel', 
        'replyCount', 'retweetCount', 'likeCount', 'quoteCount'
    ]]
    for col in ['id', 'conversationId', 'userId']:
        df[col] = df[col].apply(lambda x: int(x))
    df['date'] = df.date.apply(lambda x: pd.to_datetime(x))

    # Clear Users Dataframe
    users_df['userId'] = users_df.id
    users_df = users_df[[
        'userId', 'username', 'displayname', 'description', 'created', 'verified', 'protected',
        'followersCount', 'friendsCount', 'statusesCount', 'favouritesCount', 'listedCount', 'mediaCount',
        'linkUrl', 'linkTcourl', 'profileImageUrl', 'profileBannerUrl', 'url'
    ]]
    users_df['userId'] = users_df.userId.apply(lambda x: int(x))
    users_df['created'] = users_df.created.apply(lambda x: pd.to_datetime(x))
    users_df = users_df.drop_duplicates('userId').reset_index(drop=True)

    return users_df, df

# Loop through data to append results
comments = pd.DataFrame([]); users = pd.DataFrame([])
files = glob.glob('./data/raw/*.parquet')
for file in files:
    users_df, df = render_df(file)
    comments = comments.append(df)
    users = users.append(users_df)
    print('Finished processing', file)
users = users.drop_duplicates('userId')

# Saving comments and data files
comments.to_parquet('./data/interim/covid-tweet-comments.parquet', index=False, compression='gzip')
users.to_parquet('./data/interim/covid-tweet-users.parquet', index=False, compression='gzip')