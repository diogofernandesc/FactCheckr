from db_engine import DBConnection
from cons import DB, TWEET


class Human(object):
    def __init__(self):
        self.db_connection = DBConnection()

    def label(self, label=False, fact_checking=False):
        '''

        :param label: Determine whether worth fact-checking
        :param fact_checking: Determine the truth of it
        :return:
        '''
        start_epoch = 1520812800
        # tweet_test = list(self.db_connection.get_random_sample(collection=DB.RELEVANT_TWEET_COLLECTION,
        #                                                   query={"$and":[{"crowdsourced": {"$exists": False}},
        #                                                                  {"created_at_epoch": {"$gt": start_epoch}}]},
        #                                                   size=100))
        #
        # tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
        #                                           filter={"$and":[{"crowdsourced": {"$exists": False}},
        #                                                           {"created_at_epoch": {"$gt": start_epoch}}]},
        #                                           projection={"text": 1})

        # print tweet_test.count()
        # print tweets.count()
        # print tweet_test[0]['text']
        # # for tweet in tweet_test:
        # #     print tweet['text']
        # #     break
        # print tweets[0]['text']
        #     # print tweet['text']

        bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
        bulk_count = 0
        if label:
            # tweets = list(self.db_connection.get_random_sample(collection=DB.RELEVANT_TWEET_COLLECTION,
            #                                                    query={"$and": [{"crowdsourced": {"$exists": False}},
            #                                                                   {TWEET.SET_TO_FACTCHECK:
            #                                                                        {"$exists": False}}]},
            #                                                    size=500))

            tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                      filter={"$and": [{"crowdsourced": {"$exists": False}},
                                                                       {TWEET.SET_TO_FACTCHECK: {"$exists": False}}]},
            #                                                                   {TWEET.SET_TO_FACTCHECK,
                                                      projection={"text": 1}, sort=True, sort_field="retweet_count", limit=500)

            for tweet in tweets:
                print tweet['text']
                worth = raw_input()
                if worth == "y":
                    self.db_connection.add_to_bulk_upsert(query={"_id": tweet["_id"]},
                                                          data={TWEET.SET_TO_FACTCHECK: True},
                                                          bulk_op=bulk_op)


                else:
                    self.db_connection.add_to_bulk_upsert(query={"_id": tweet["_id"]},
                                                          data={TWEET.SET_TO_FACTCHECK: False},
                                                          bulk_op=bulk_op)

                bulk_count += 1
                print "\n"

                if bulk_count != 0 and bulk_count % 100 == 0:
                    self.db_connection.end_bulk_upsert(bulk_op=bulk_op)
                    bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)

        if fact_checking:
            tweets = list(self.db_connection.get_random_sample(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                               query={"$and": [{"crowdsourced": {"$exists": False}},
                                                                              {TWEET.SET_TO_FACTCHECK: True}]},
                                                               size=100))

            for tweet in tweets:
                print tweet['text']
                rating = raw_input()
                self.db_connection.add_to_bulk_upsert(query={"_id": tweet["_id"]},
                                                      data={TWEET.LABEL: rating == " "},
                                                      bulk_op=bulk_op)
                print "---\n"
                bulk_count += 1

                if bulk_count % 100 == 0:
                    self.db_connection.end_bulk_upsert()
                    bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)

        if bulk_count != 0 and bulk_count % 100 == 0:
            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)

human = Human()
human.label(label=True)