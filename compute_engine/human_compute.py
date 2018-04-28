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

    def entity_measure(self):
        tp = 0
        tn = 0
        fp = 0
        fn = 0
        count = 0
        try:
            tweets = self.db_connection.get_random_sample(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                              query={"$and": [
                                                                  {TWEET.SET_TO_FACTCHECK: True},
                                                                  {TWEET.ENTITIES_COUNT: {"$eq": 1}}
                                                              ]}, size=1)

            total = 5
            for tweet in tweets:

                print tweet['text']
                print '----ENTITIES----'
                entities = [x['entity'] for x in tweet['entities']]
                print entities
                print '----INPUT-------'

                tp_input = int(raw_input("Is an entity and API says it's an entity\n"))
                if tp_input == 0:
                    fp += 1

                tn_input = int(raw_input("Is not an entity, API says it's not an entity\n"))
                fn_input = int(raw_input("Is an entity, API says it's not \n"))
                print "\n\n\n"

                tp += tp_input
                tn += tn_input
                fn += fn_input
                count += 1
                total -= 1
                print "total: %s" % total

            print "tp: %s" % tp
            print "tn: %s" % tn
            print "fp: %s" % fp
            print "fn: %s" % fn

        except Exception as e:
            print e
            print "count: %s" % count
            print "tp: %s" % tp
            print "tn: %s" % tn
            print "fp: %s" % fp
            print "fn: %s" % fn

human = Human()
# human.label(label=True)
human.entity_measure()