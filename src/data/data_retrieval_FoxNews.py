import os
import nest_asyncio
import pandas as pd
import numpy as np
from datetime import timedelta
nest_asyncio.apply()
import snscrape.modules.twitter as sntwitter
import itertools

# our search term, using syntax for Twitter's Advanced Search
page = "pacodlee"
since = '2020-01-01'
until = '2021-04-30'
search = "coronavirus covid since:{} until:{} filter:news filter:verified filter:has_engagement lang:en".format(since, until)
tmp = pd.DataFrame(itertools.islice(sntwitter.TwitterSearchScraper(search).get_items(), None))
tmp.shape

tmp.to_csv('sbs_sample.csv')

# # the scraped tweets, this is a generator
# scraped_tweets = sntwitter.TwitterSearchScraper(search).get_items()

# # slicing the generator to keep only the first 100 tweets
# sliced_scraped_tweets = itertools.islice(scraped_tweets, 100)

# # convert to a DataFrame and keep only relevant columns
# df = pd.DataFrame(sliced_scraped_tweets)[['date', 'lang']]
# print("Data shape:", df.shape)
# print(df.iloc[0])

# # # Important variables to be used
# since = '2020-01-01'
# until = '2021-03-01'

# # # Retrieving content using snscrape
# # page = 'FoxNews'
# os.system("snscrape --since {} twitter-search \"from:{} until:{}\" > {}.json".format(
#     since, page, until, page
# ))

# # Consolidating everything in one file
# df = pd.read_json(page+'.json', lines=True)
# print("Data shape:", df.shape)