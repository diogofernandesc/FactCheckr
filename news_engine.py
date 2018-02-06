from datetime import datetime
from newsapi import NewsApiClient
from db_engine import DBConnection
import os
from cons import NEWS_HEADLINE, NEWS_CATEGORIES


class NewsClient(object):
    def __init__(self):
        self.api = NewsApiClient(api_key=os.getenv("NEWS_API_KEY"))
        self.db_connection = DBConnection()

    def get_top_headlines(self, language='en', country='gb', query=None):
        categories_of_interest = [NEWS_CATEGORIES.BUSINESS, NEWS_CATEGORIES.GENERAL,
                                  NEWS_CATEGORIES.HEALTH, NEWS_CATEGORIES.SCIENCE]

        for cat in categories_of_interest:
            headlines_to_insert = []
            top_headlines = self.api.get_top_headlines(q=query, category=cat, language=language,
                                                       country=country, page_size=100)

            total_results = top_headlines["totalResults"]
            for headline in top_headlines['articles']:
                date = datetime.strptime(headline["publishedAt"], '%Y-%m-%dT%H:%M:%SZ')
                headlines_to_insert.append({
                    NEWS_HEADLINE.DESCRIPTION: headline["description"],
                    NEWS_HEADLINE.TITLE: headline["title"],
                    NEWS_HEADLINE.URL: headline["url"],
                    NEWS_HEADLINE.AUTHOR: headline["source"]["name"],
                    NEWS_HEADLINE.PUBLISH_DATE: date,
                    NEWS_HEADLINE.CATEGORY: cat
                })

            self.db_connection.insert_news_headlines(headlines_to_insert)


client = NewsClient()
client.get_top_headlines()