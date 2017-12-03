import unittest
from db_engine import DBConnection
from twitter_engine import Twitter
from cons import DB, CREDS
import os


class DBFindTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_find_document(self):
        db_connection = DBConnection()
        result = db_connection.find_document(collection=DB.MP_COLLECTION,
                                             filter={"twitter_handle": "@theresa_may"},
                                             projection={"name": 1, "_id": 0})[0]

        db_connection.close()
        self.assertEqual(result["name"], "Theresa May")

    def test_validate_twitter(self):
        db_connection = DBConnection()
        twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
                              os.environ.get(CREDS.TWITTER_SECRET),
                              os.environ.get(CREDS.TWITTER_TOKEN),
                              os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
                              db_connection)

        self.assertTrue(expr=twitter_api.verify_credentials(), msg="Could not validate Twitter credentials.")


if __name__ == '__main__':
    unittest.main()
