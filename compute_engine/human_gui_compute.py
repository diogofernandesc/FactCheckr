import Tkinter as tk
from cons import DB, TWEET
from db_engine import DBConnection

class HumanComputeGUIEntity(tk.Frame):

    def __init__(self, parent):
        self.db_connection = DBConnection()
        self.bulk_count = 0

        tk.Frame.__init__(self, parent)
        # create a prompt, an input box, an output label,
        # and a button to do the computation
        self.prompt = tk.Label(self, text="Enter a number:", anchor="w", wraplength=500)
        self.entities_prompt = tk.Label(self, text="entities", anchor="w", wraplength=500)
        # self.entry = tk.Entry(self)
        self.tp = tk.Button(self, text="Is an entity and API says it's an entity", command=self.calculate1)
        self.tn = tk.Button(self, text="Is not an entity, API does not include it", command=self.calculate2)
        self.fp = tk.Button(self, text='Is not an entity, API includes it', command=self.calculate3)
        self.fn = tk.Button(self, text='Is an entity, API does not include it', command=self.calculate4)
        self.output = tk.Label(self, text="")

        # lay the widgets out on the screen.
        self.prompt.pack(side="top", fill="x")
        self.entities_prompt.pack(side="bottom")
        # self.entry.pack(side="top", fill="x", padx=20)
        self.output.pack(side="top", fill="x", expand=True)
        self.fn.pack(side="bottom")
        self.fp.pack(side="bottom")
        self.tn.pack(side="bottom")
        self.tp.pack(side="bottom")

        self.tweets = self.db_connection.get_random_sample(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                           query={"$and": [
                                                               {TWEET.SET_TO_FACTCHECK: True},
                                                               {TWEET.ENTITIES_COUNT: {"$eq": 1}}
                                                           ]}, size=200)

        self.current = self.tweets.next()
        self.prompt.configure(text=self.current["text"])
        self.entities_prompt.configure(text="Entities: %s" % [x['entity'] for x in self.current["entities"]])
        self.tp = 0
        self.tn = 0
        self.fp = 0
        self.fn = 0

        # for tweet in tweets:

    def calculate1(self):
        try:

            self.tp += 1
            self.current = self.tweets.next()
            if self.current:
                self.prompt.configure(text=self.current['text'].encode('ascii', 'ignore'))
                self.entities_prompt.configure(text="Entities: %s" % [x['entity'] for x in self.current["entities"]])

            else:
                print "tp: %s" % self.tp
                print "tn: %s" % self.tn
                print "fp: %s" % self.fp
                print "fn: %s" % self.fn

        except Exception as e:
            print e
            print "tp: %s" % self.tp
            print "tn: %s" % self.tn
            print "fp: %s" % self.fp
            print "fn: %s" % self.fn

    def calculate2(self):
        try:

            self.tn += 1
            self.current = self.tweets.next()
            if self.current:
                self.prompt.configure(text=self.current['text'].encode('ascii', 'ignore'))
                self.entities_prompt.configure(text="Entities: %s" % [x['entity'] for x in self.current["entities"]])

            else:
                print "tp: %s" % self.tp
                print "tn: %s" % self.tn
                print "fp: %s" % self.fp
                print "fn: %s" % self.fn
        except Exception as e:
            print e
            print "tp: %s" % self.tp
            print "tn: %s" % self.tn
            print "fp: %s" % self.fp
            print "fn: %s" % self.fn

    def calculate3(self):
        try:

            self.fp += 1
            self.current = self.tweets.next()
            if self.current:
                self.prompt.configure(text=self.current['text'].encode('ascii', 'ignore'))
                self.entities_prompt.configure(text="Entities: %s" % [x['entity'] for x in self.current["entities"]])

            else:
                print "tp: %s" % self.tp
                print "tn: %s" % self.tn
                print "fp: %s" % self.fp
                print "fn: %s" % self.fn
        except Exception as e:
            print e
            print "tp: %s" % self.tp
            print "tn: %s" % self.tn
            print "fp: %s" % self.fp
            print "fn: %s" % self.fn

    def calculate4(self):
        try:

            self.fn += 1
            self.current = self.tweets.next()
            if self.current:
                self.prompt.configure(text=self.current['text'].encode('ascii', 'ignore'))
                self.entities_prompt.configure(text=[x['entity'] for x in self.current["entities"]])

            else:
                print "tp: %s" % self.tp
                print "tn: %s" % self.tn
                print "fp: %s" % self.fp
                print "fn: %s" % self.fn
        except Exception as e:
            print e
            print "tp: %s" % self.tp
            print "tn: %s" % self.tn
            print "fp: %s" % self.fp
            print "fn: %s" % self.fn


    def label(self, label=False, fact_checking=False):
        '''

        :param label: Determine whether worth fact-checking
        :param fact_checking: Determine the truth of it
        :return:
        '''
        start_epoch = 1520812800

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
                                                      projection={"text": 1}, sort=True, sort_field="retweet_count",
                                                      limit=500)

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

                self.bulk_count += 1
                print "\n"

                if self.bulk_count != 0 and self.bulk_count % 100 == 0:
                    self.db_connection.end_bulk_upsert(bulk_op=bulk_op)
                    bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)

        # if fact_checking:
        #     tweets = list(self.db_connection.get_random_sample(collection=DB.RELEVANT_TWEET_COLLECTION,
        #                                                        query={"$and": [{"crowdsourced": {"$exists": False}},
        #                                                                        {TWEET.SET_TO_FACTCHECK: True}]},
        #                                                        size=100))
        #
        #     for tweet in tweets:
        #         print tweet['text']
        #         rating = raw_input()
        #         self.db_connection.add_to_bulk_upsert(query={"_id": tweet["_id"]},
        #                                               data={TWEET.LABEL: rating == " "},
        #                                               bulk_op=bulk_op)
        #         print "---\n"
        #         bulk_count += 1
        #
        #         if bulk_count % 100 == 0:
        #             self.db_connection.end_bulk_upsert()
        #             bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
        #
        if self.bulk_count != 0 and self.bulk_count % 100 == 0:
            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)

# if this is run as a program (versus being imported),
# create a root window and an instance of our example,
# then start the event loop

if __name__ == "__main__":
    root = tk.Tk()
    HumanComputeGUIEntity(root).pack(fill="both", expand=True)
    root.mainloop()