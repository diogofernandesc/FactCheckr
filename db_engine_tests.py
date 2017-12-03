import unittest
from db_engine import DBConnection
from twitter_engine import Twitter
from cons import DB, CREDS
import os


class DBFindTest(unittest.TestCase):

    def setUp(self):
        self.db_connection = DBConnection()

    def tearDown(self):
        self.db_connection.close()

    def test_find_document(self):
        result = self.db_connection.find_document(collection=DB.MP_COLLECTION,
                                             filter={"twitter_handle": "@theresa_may"},
                                             projection={"name": 1, "_id": 0})

        self.assertEqual(result[0]["name"], "Theresa May")

    # def test_validate_twitter(self):
    #     twitter_api = Twitter(os.getenv(CREDS.TWITTER_KEY),
    #                           os.getenv(CREDS.TWITTER_SECRET),
    #                           os.getenv(CREDS.TWITTER_TOKEN),
    #                           os.getenv(CREDS.TWITTER_TOKEN_SECRET),
    #                           self.db_connection)
    #
    #     self.assertTrue(expr=twitter_api.verify_credentials(), msg="Could not validate Twitter credentials.")


if __name__ == '__main__':
    unittest.main()
