import sys
sys.path.append("..")
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

    def get_top_articles(self, time_collect=None, historic=False):
        if not historic:
            time_collect = datetime.now() - timedelta(days=1)

        results = self.api.top_articles(project=WIKI_SOURCES.ENGLISH_WIKIPEDIA,
                                        year=time_collect.year, month=time_collect.month, day=time_collect.day)

        timestamp = calendar.timegm(time_collect.timetuple())
        articles_to_insert = []
        bulk_op = None
        if historic:
            bulk_op = self.db_connection.start_bulk_upsert(collection=DB.WIKI_TRENDS)
        for result in results:
            name = result["article"]
            if "_" in name:
                name = name.replace("_", " ")

            doc = {
                WIKI_TREND.NAME: name,
                WIKI_TREND.RANK: int(result["rank"]),
                WIKI_TREND.VIEWS: int(result["views"]),
                WIKI_TREND.TIMESTAMP: timestamp,
                WIKI_TREND.DATE_OBJECT: time_collect,
                WIKI_TREND.DATE_STRING: time_collect.strftime("%A %B %d %Y"),
                WIKI_TREND.MONTH: time_collect.strftime("%B").lower(),
                WIKI_TREND.WEEKDAY: time_collect.strftime("%A").lower(),
                WIKI_TREND.MONTH_DAY: int(time_collect.strftime("%d")),
                WIKI_TREND.YEAR: time_collect.strftime("%Y")
            }

            if historic:
                self.db_connection.add_to_bulk_upsert(query={"$and": [{WIKI_TREND.NAME: name},
                                                    {WIKI_TREND.DATE_STRING: time_collect.strftime("%A %B %d %Y")}]},
                                                    data=doc, bulk_op=bulk_op)

            else:
                articles_to_insert.append(doc)

        if historic:
            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)

        else:
            self.db_connection.bulk_insert(data=articles_to_insert, collection=DB.WIKI_TRENDS)


if __name__ == "__main__":
    wiki_ingest = WikiIngest()
    while True:
        # wiki_ingest.get_top_articles()
        yesterday = datetime.now() - timedelta(days=1)
        if "historic" not in sys.argv:
            wiki_ingest.logger.info("Getting wikipedia trends for month: %s, day: %s, hour: %s" % (yesterday.month,
                                                                                                   yesterday.day,
                                                                                                   yesterday.hour))
            wiki_ingest.get_top_articles()
            time.sleep(60 * 60 * 24)

        # Get historic
        start = datetime(year=2018, month=1, day=1)
        wiki_ingest.logger.info("Getting HISTORIC wikipedia trends for month: %s, day: %s, hour: %s" % (start.month,
                                                                                                        start.day,
                                                                                                        start.hour))
        wiki_ingest.get_top_articles(time_collect=start, historic=True)
        start = start + timedelta(days=1)
        if start > yesterday:
            break