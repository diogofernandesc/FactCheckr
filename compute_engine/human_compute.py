from db_engine import DBConnection
from cons import DB


class Human(object):
    def __init__(self):
        self.db_connection = DBConnection()

    def label(self):
        # tweets = self.db_connection.find_document(collection=DB.TWEET_COLLECTION,
        #                                           filter={"relevancy_week": {"$exists": True}},
        #                                           projection={"text": 1})

        user_input = raw_input("enter your choice:")
        print user_input


human = Human()
human.label()