ugpn-covid-emotions
==============================

Analysis of emotions/sentiments from general public to news related to COVID-19 on Twitter.

- data/processed/ contains the data used in this paper, separated by year and month in yyyy-mm format. The data sets doesn't contain any Twitter content, following Twitter Inc. guidelines. If you want to reproduce the results, please hydrate using the "tweetId" column.
- src/data/ contains the code used to scrape tweets through the usage of "snscrape" Python library. Please consider if snscrape is deprecated.
- notebooks/ contains the code used to (i) LDA topic modeling, (ii) RoBERTa emotion score computing, and (iii) figures and tables generation. 

Please refer to /data/data_sample.csv to see a sample of data used in this work (as for data schema, features, etc).
