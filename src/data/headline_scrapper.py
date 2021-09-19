'''
headline_scraper.py
A simple scrapy spider to collect web page titles
'''

import scrapy
from pandas import read_csv
from readability.readability import Document

PATH_TO_DATA = './notebooks/fox_news_headlines.csv'

import logging

logging.basicConfig(
    filename='log.txt',
    format='%(levelname)s: %(message)s',
    level=logging.INFO
)

class HeadlineSpider(scrapy.Spider):
    name = "headline_spider"
    start_urls = read_csv(PATH_TO_DATA).url.tolist()
    counter = -1

    def parse(self, response):
        self.counter = self.counter + 1
        doc = Document(response.text)
        yield {
            'short_title': doc.short_title(),
            'full_title': doc.title(),
            'url': response.url
        }