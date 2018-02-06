from pymongo import MongoClient, bulk
from scraper_engine import Scraper
from cons import DB
import os
import logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class DBConnection(object):
    def __init__(self):
        # value = os.getenv("USER_MONGO")
        self.client = MongoClient("mongodb://%s:%s@%s:27017" % (
            os.getenv("USER_MONGO"),
            os.getenv("PASS_MONGO"),
            os.getenv("ADDRESS_MONGO")
            ))

        # Testing:
        # self.client = MongoClient("mongodb://localhost:27017")
        # self.scraper = Scraper("http://www.mpsontwitter.co.uk/list")
        self.db = self.client.ip_db
        self.bulkWrite = []
        self.logger = logging.getLogger(__name__)

    def insert_tweets(self, tweet_list, retweets=False):
        try:
            collection = DB.TWEET_COLLECTION
            if retweets:
                collection = DB.RETWEET_COLLECTION

            bulk_insert = bulk.BulkOperationBuilder(collection=self.db[collection], ordered=False)
            for tweet in tweet_list:
                bulk_insert.insert(tweet)

            response = bulk_insert.execute()

        except:
            self.logger.info("Duplicate insertion ignored")

    def insert_news_headlines(self, headline_list):
        try:
            collection = DB.NEWS_COLLECTION
            bulk_insert = bulk.BulkOperationBuilder(collection=self.db[collection], ordered=False)
            for headline in headline_list:
                bulk_insert.insert(headline)

            response = bulk_insert.execute()

        except Exception as e:
            self.logger.info("Avoided inserting duplicate news headline")

        # self.db[DB.TWEET_COLLECTION].insert_many(tweet_list, ordered=False)

    def apply_field_to_all(self, field, value, collection):
        result = self.db[collection].update_many({"author_handle": "@AdamAfriyie"}, {'$set': {field: value}})
        print result.matched_count

    def insert_tweet(self, tweet):
        self.db[DB.TWEET_COLLECTION].insert_one(tweet)

    # def insert_mps(self):
        # mp_list = self.scraper.scrape_page()
        # mp_data = self.db.mp_data
        # result = mp_data.insert_many(mp_list)

    def start_bulk_write(self):
        self.bulkWrite = []

    def end_bulk_write(self, collection, ordered=False):
        try:
            self.db[collection].bulk_write(self.bulkWrite, ordered=ordered)
            self.bulkWrite = []
        except self.client.BulkWriteError as bwe:
            print(bwe.details)

    def find_document(self, collection, filter=None, projection=None):
        return self.db[collection].find(filter=filter, projection=projection, no_cursor_timeout=False)

    def find_and_update(self, collection, query=None, update=None):
        result = self.db[collection].update_one(query, update)
        return result

    def create_mp(self, data):
        mp_data = self.db.mp_data
        result = mp_data.insert_one(data)

    def update_mp(self, user_id, update):
        '''
        Updates fields for a given MP
        :param user_id: twitter id of the MP
        :param update: The fields being updated or inserted
        :return: Adds this to the bulk list of operations to perform
        '''

        mp_data = self.db.mp_data
        result = mp_data.update_one(filter={"_id": user_id}, update={"$set": update}, upsert=True)
        # self.bulkWrite.append(result)

    def close(self):
        self.client.close()




