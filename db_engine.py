from pymongo import MongoClient
from scraper_engine import Scraper
from cons import DB
import os


class DBConnection(object):
    def __init__(self, deploy=False):
        print os.environ.get("MONGO_URI")
        self.client = MongoClient(os.environ.get("MONGO_URI"))
        self.scraper = Scraper("http://www.mpsontwitter.co.uk/list")
        self.db = self.client.ip_db
        self.bulkWrite = []

    def insert_mps(self):
        mp_list = self.scraper.scrape_page()
        mp_data = self.db.mp_data
        result = mp_data.insert_many(mp_list)

    def start_bulk_write(self):
        self.bulkWrite = []

    def end_bulk_write(self, collection, ordered=False):
        try:
            self.db[collection].bulk_write(self.bulkWrite, ordered=ordered)
            self.bulkWrite = []
        except self.client.BulkWriteError as bwe:
            print(bwe.details)

    def find_document(self, collection, filter=None, projection=None):
        return self.db[collection].find(filter=filter, projection=projection)

    def find_and_update(self, collection, filter=None, update=None):
        self.db[collection].find_one_and_update(filter=filter, update=update)

    def create_mp(self, data):
        mp_data = self.db.mp_data
        result = mp_data.insert_one(data)

    def update_mp(self,user_id, update):
        '''
        Updates fields for a given MP
        :param user_id: twitter id of the MP
        :param update: The fields being updated or inserted
        :return: Adds this to the bulk list of operations to perform
        '''

        mp_data = self.db.mp_data
        result = mp_data.update_one(filter={"_id": user_id}, update={"$set": update}, upsert=True)
        # self.bulkWrite.append(result)

    # def get_db_credentials(self):
    #     with open("creds.txt", "r") as creds:
    #         for line in creds:
    #             if line.startswith("!db"):
    #                 creds = line.split("-->")[1]
    #                 return creds

    def close(self):
        self.client.close()


db = DBConnection()

db.close()




