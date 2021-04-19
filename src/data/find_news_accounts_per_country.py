# Libraries
from collections import Counter
import pandas as pd
from pathlib import Path
import snscrape.modules.twitter as sntwitter
import itertools
import math

# Functions
def get_mentioned_users(x):
    users = []
    try:
        for i in range(len(x)):
            users = users + [x[i]['username']]
    except:
        pass
    return users

# Selected locations
# Source: https://en.wikipedia.org/wiki/List_of_countries_by_English-speaking_population (>1MM native speakers)
locations = {
    'east_us': '35.672964,-79.039292,1200km',
    'central_us': '38.273120,-98.582187,1200km',
    'west_us': '39.515882,-116.853723,1100km',
    'ireland_uk': '54.521992,-3.984398,550km',
    'east_canada': '53.685485,-79.787644,1150km',
    'west_canada': '58.276278,-115.796203,1150km',
    'australia': '-25.610118, 134.354805,2100km',
    'south_africa': '-28.816624, 24.991639,1000km',
    'ireland': '52.812761,-8.703998,200km',
    'new_zeland': '-41.500083,172.834408,830km',
    'sri_lanka': '7.555494,80.713785, 265km',
    'singapore': '1.271988,103.823620,22km',
    'trinidad_tobago': '10.695211,-61.168652,100km'
}

# Query constants
since = '2020-01-01'
until = '2021-03-01'
keywords = '(wuhan OR ncov OR coronavirus OR covid OR sars-cov-2 OR pandemic)'
project_dir = Path(__file__).resolve().parents[2]

# Loop to find media
for place in locations.keys():
    print('Start processing', place)
    loc = locations[place]
    df = pd.DataFrame(itertools.islice(sntwitter.TwitterSearchScraper(
        '{} since:{} until:{} geocode:"{}"'.format(keywords, since, until, loc)).get_items(), 100000))
    df['username'] = df.user.apply(lambda x: x['username'])
    print(place, ':initial referential timestamp:', df.date.min())

    users = (list(itertools.chain.from_iterable(df.mentionedUsers.apply(lambda x: get_mentioned_users(x)))))
    users = pd.DataFrame(Counter(users).items(), columns=['account', 'count'])
    users = users[users['count']>math.ceil(df.shape[0]/5000)].sort_values('count', ascending=False).reset_index(drop=True)
    print(place, ':number of selected users:', users.shape[0])

    selected_users = pd.DataFrame([], columns=[
        'username', 'cnt', 'description', 'verified', 'followersCount', 'statusesCount', 'mediaCount'])
    for i in range(users.shape[0]):
        try:
            ent = sntwitter.TwitterUserScraper(users.iloc[i].account).entity
            selected_users.loc[selected_users.shape[0]] = [
                ent.username, users.iloc[i]['count'], ent.description, ent.verified, ent.followersCount, ent.statusesCount, ent.mediaCount]
            if i%10==0:
                print('Got info from user:',i)
        except:
            print('Got an error from user:', i)
            pass
    selected_users = selected_users[(selected_users.description.apply(lambda x: any(word in x for word in ('news', 'News')))) & (selected_users.verified)]
    selected_users.to_csv('./data/interim/'+place+'_media.csv')