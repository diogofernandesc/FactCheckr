import logging
import os

from pymongo import MongoClient, bulk
from pymongo.errors import DuplicateKeyError

from cons import DB

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class DBConnection(object):
    def __init__(self):
        self.client = MongoClient("mongodb://%s:%s@%s:27017" % (
            os.getenv("USER_MONGO"),
            os.getenv("PASS_MONGO"),
            os.getenv("ADDRESS_MONGO")
            ))

        # Testing:
        # self.client = MongoClient("mongodb://localhost:27017")
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

        except Exception as e:
            self.logger.info("Duplicate insertion ignored")

    def insert_news_article(self, article):
        news_collection = self.db.news_articles
        try:
            result = news_collection.update_one(filter={"url": article["url"]}, update={"$set": article}, upsert=True)
        except DuplicateKeyError as e:
            pass

    def bulk_insert(self, data, collection):
        """
        Bulk insert when data is NOT tweets
        :param data: payload to insert
        :param collection: mongo collection to insert in
        :return:
        """
        try:
            bulk_insert = bulk.BulkOperationBuilder(collection=self.db[collection], ordered=False)
            for item in data:
                bulk_insert.insert(item)

            response = bulk_insert.execute()

        except Exception as e:
            if collection == DB.NEWS_ARTICLES:
                self.logger.info("Avoided inserting duplicate news articles")

            elif collection == DB.SOURCES_COLLECTION:
                self.logger.info("Avoided insert duplicate news source")

    def apply_field_to_all(self, field, value, collection):
        result = self.db[collection].update_many({}, {'$set': {field: value}}, upsert=True)
        self.logger.info(result.matched_count)

    def insert_tweet(self, tweet):
        self.db[DB.TWEET_COLLECTION].insert_one(tweet)

    def start_bulk_write(self):
        self.bulkWrite = []

    def end_bulk_write(self, collection, ordered=False):
        try:
            self.db[collection].bulk_write(self.bulkWrite, ordered=ordered)
            self.bulkWrite = []
        except self.client.BulkWriteError as bwe:
            self.logger.warning(bwe.details)

    def find_document(self, collection, filter=None, projection=None, limit=0):
        return self.db[collection].find(filter=filter, projection=projection, no_cursor_timeout=True, limit=limit)

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

    def update_tweet(self, tweet_id, update):
        tweet_data = self.db.mp_tweets
        result = tweet_data.update_one(filter={"_id": tweet_id}, update={"$set": update}, upsert=False)
        print result

    def close(self):
        self.client.close()




