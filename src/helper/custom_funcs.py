import os

#
def get_user_dict(user):
    return {
        'userId':user.id,
        'username':user.username,
        'displayname':user.displayname,
        'description':user.description,
        'descriptionUrls':user.descriptionUrls,
        'verified':user.verified,
        'created':user.created,
        'location':user.location,
        'protected':user.protected,
        'linkUrl':user.linkUrl,
        'followersCount':user.followersCount,
        'friendsCount':user.friendsCount,
        'statusesCount':user.statusesCount,
        'favouritesCount':user.favouritesCount,
        'listedCount':user.listedCount,
        'mediaCount':user.mediaCount
    }

#
def get_page_covid_content(search):
    
    # Get temporary dataframe from collect
    df = pd.DataFrame(itertools.islice(sntwitter.TwitterSearchScraper(search).get_items(), 100))
    df = df.rename(columns={'id':'tweetId'})
    users_df = pd.DataFrame(list(df.user.values))
    users_df = users_df.rename(columns={'id':'userId'})
    df['userId'] = users_df['userId']
    users_df = users_df.drop_duplicates('id')
    df = df[[
        'tweetId', 'conversationId', 'userId', 'date', 'content', 'lang', 'sourceLabel', 
        'replyCount', 'retweetCount', 'likeCount', 'quoteCount', 'coordinates', 'place'
    ]]
    
    return df, users_df

def check_page(page):
    return os.path.exists('./data/raw/' + page + '.parquet')