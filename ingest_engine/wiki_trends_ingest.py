from db_engine import DBConnection
from mwviews.api import PageviewsClient
from datetime import datetime, timedelta
import calendar
from cons import WIKI_SOURCES, WIKI_TREND, DB
import time
import logging
import os

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class WikiIngest(object):
    def __init__(self):
        self.db_connection = DBConnection()
        self.logger = logging.getLogger(__name__)
        self.api = PageviewsClient("Mozilla/5.0 (X11; Linux x86_64)"
                                   " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36")

    def get_top_articles(self):
        yesterday = datetime.now() - timedelta(days=1)
        timestamp = calendar.timegm(yesterday.timetuple())
        results = self.api.top_articles(project=WIKI_SOURCES.ENGLISH_WIKIPEDIA,
                                        year=yesterday.year, month=yesterday.month, day=yesterday.day)

        articles_to_insert = []
        for result in results:
            name = result["article"]
            if "_" in name:
                name = name.replace("_", " ")

            articles_to_insert.append({
                WIKI_TREND.NAME: name,
                WIKI_TREND.RANK: int(result["rank"]),
                WIKI_TREND.VIEWS: int(result["views"]),
                WIKI_TREND.TIMESTAMP: timestamp,
                WIKI_TREND.DATE_OBJECT: yesterday,
                WIKI_TREND.DATE_STRING: yesterday.strftime("%A %B %d %Y"),
                WIKI_TREND.MONTH: yesterday.strftime("%B").lower(),
                WIKI_TREND.WEEKDAY: yesterday.strftime("%A").lower(),
                WIKI_TREND.MONTH_DAY: int(yesterday.strftime("%d")),
                WIKI_TREND.YEAR: yesterday.strftime("%Y")
            })
        self.db_connection.bulk_insert(data=articles_to_insert, collection=DB.WIKI_TRENDS)


if __name__ == "__main__":
    wiki_ingest = WikiIngest()
    while True:
        wiki_ingest.get_top_articles()
        yesterday = datetime.now() - timedelta(days=1)
        wiki_ingest.logger.info("Getting wikipedia trends for month: %s, day: %s, hour: %s" % (yesterday.month,
                                                                                               yesterday.day,
                                                                                               yesterday.hour))
        time.sleep(60*60*24)