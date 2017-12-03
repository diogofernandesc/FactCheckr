import unittest
from db_engine import DBConnection
from cons import DB


class DBFindTest(unittest.TestCase):

    def find_document(self):
        db_connection = DBConnection(deploy=True)
        result = db_connection.find_document(collection=DB.MP_COLLECTION,
                                             filter={"twitter_handle": "@theresa_may"},
                                             projection={"name": 1, "_id": 0})[0]

        self.assertEqual(result["name"], "Theresa May")
        db_connection.close()


if __name__ == '__main__':
    unittest.main()
