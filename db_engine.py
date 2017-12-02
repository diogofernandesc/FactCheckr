from pymongo import MongoClient
from scraper_engine import Scraper
from cons import DB


class DBConnection(object):
    def __init__(self):
        self.mongo_uri = self.get_db_credentials()
        self.client = MongoClient(self.mongo_uri.strip())
        self.scraper = Scraper("http://www.mpsontwitter.co.uk/list")
        self.db = self.client.ip_db

    def insert_mps(self):
        mp_list = self.scraper.scrape_page()
        mp_data = self.db.mp_data
        # result = mp_data.insert_one({"test": 1})
        result = mp_data.insert_many(mp_list)

    def get_db_credentials(self):
        with open("creds.txt", "r") as creds:
            for line in creds:
                if line.startswith("!db"):
                    creds = line.split("-->")[1]
                    return creds

    def close(self):
        self.client.close()


# db_credentials = get_db_credentials()
# print db_credentials
# db = DBConnection(db_credentials[0], db_credentials[1])
db = DBConnection()




