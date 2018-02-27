import sys
sys.path.append("..")
from datetime import datetime, timedelta
import time
import re
from newsapi import NewsApiClient
from db_engine import DBConnection
import os
from cons import NEWS_ARTICLE, NEWS_CATEGORIES, NEWS_API_PARAMS, NEWS_SOURCE, NEWS_COUNTRIES, DB
import logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class NewsClient(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
        self.db_connection = DBConnection()

    def get_sources(self):
        '''
        Get all the sources used by NEWSAPI to insert into database
        :return:
        '''
        sources = self.api.get_sources()
        sources = sources[NEWS_API_PARAMS.SOURCE]
        sources_to_insert = []
        for source in sources:
            if source[NEWS_SOURCE.COUNTRY] in [NEWS_COUNTRIES.UK, NEWS_COUNTRIES.USA]:
                sources_to_insert.append({
                    NEWS_SOURCE.DESCRIPTION: source[NEWS_SOURCE.DESCRIPTION],
                    NEWS_SOURCE.CATEGORY: source[NEWS_SOURCE.CATEGORY],
                    NEWS_SOURCE.COUNTRY: source[NEWS_SOURCE.COUNTRY],
                    NEWS_SOURCE.LANGUAGE: source[NEWS_SOURCE.LANGUAGE],
                    NEWS_SOURCE.NAME: source[NEWS_SOURCE.NAME],
                    NEWS_SOURCE.URL: source[NEWS_SOURCE.URL],
                    NEWS_SOURCE.NEWS_API_ID: source["id"],
                    NEWS_SOURCE.NEWS_API_FRIENDLY: True
                })

        self.db_connection.bulk_insert(data=sources_to_insert, collection=DB.SOURCES_COLLECTION)

    def get_articles(self, query=None, since=None):
        """
        :param query: Query for specific articles
        :param since: Datetime of the earliest date the articles can be
        :return:
        """
        articles_to_insert = []
        batch_size = 300
        article_count = 0
        page_no = 1
        stop_words = re.compile("|".join(["sport"]))  # words, categories etc that are not important to collect

        sort_by = NEWS_API_PARAMS.SORT_BY_NEWEST
        sources = list(self.db_connection.find_document(collection=DB.SOURCES_COLLECTION,
                                                        filter={NEWS_SOURCE.COUNTRY: NEWS_COUNTRIES.UK},
                                                        projection={NEWS_SOURCE.NEWS_API_ID: 1, "_id": 0}))

        sources = map(lambda x: x[NEWS_SOURCE.NEWS_API_ID], sources)
        if query:  # Sort by relevancy instead of newest if query placed
            sort_by = NEWS_API_PARAMS.SORT_BY_RELEVANCY

        if not since:
            since = datetime.now() - timedelta(days=30)

        while True:
            news_payload = self.api.get_everything(q=query, language='en', sources=sources,
                                                   from_parameter=since, sort_by=sort_by, page=page_no,
                                                   page_size=NEWS_API_PARAMS.PAGE_SIZE)

            total_articles = None
            if "totalResults" in news_payload:
                total_articles = news_payload["totalResults"]

            if "totalResults" in news_payload:
                total_articles = news_payload["totalResults"]
            
            raw_articles = None
            if "articles" in news_payload:
                article_count += len(news_payload["articles"])
                raw_articles = news_payload["articles"]

            if raw_articles:
                for article in raw_articles:
                    if not stop_words.search(article["url"]):  # Avoid URLs with the given stop words in them
                        date = datetime.strptime(article["publishedAt"], '%Y-%m-%dT%H:%M:%SZ')
                        articles_to_insert.append({
                            NEWS_ARTICLE.DESCRIPTION: article["description"],
                            NEWS_ARTICLE.TITLE: article["title"],
                            NEWS_ARTICLE.URL: article["url"],
                            NEWS_ARTICLE.SOURCE: article["source"]["name"],
                            NEWS_ARTICLE.PUBLISH_DATE: date,
                        })

            page_no += 1

            if len(articles_to_insert) >= batch_size:
                self.db_connection.bulk_insert(data=articles_to_insert, collection=DB.NEWS_ARTICLES)
                articles_to_insert = []

            if not total_articles or article_count > total_articles:
                break


if __name__ == "__main__":
    client = NewsClient()

    # Collect articles every 12 hours
    while True:
        since = datetime.now() - timedelta(hours=12)
        client.get_articles(since=since)
        client.logger.info("Getting news articles since month: %s, day: %s, hour: %s" % (since.month,
                                                                                         since.day,
                                                                                         since.hour))
        time.sleep(60*60*4)  # sleep for 4 hours
