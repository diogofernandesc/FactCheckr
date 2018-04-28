import Tkinter as tk
from cons import DB, TWEET
from db_engine import DBConnection

class HumanComputeGUI(tk.Frame):

    def __init__(self, parent):
        self.db_connection = DBConnection()
        self.bulk_count = 0

        tk.Frame.__init__(self, parent)
        # create a prompt, an input box, an output label,
        # and a button to do the computation
        self.prompt = tk.Label(self, text="Enter a number:", anchor="w", wraplength=500)
        # self.entry = tk.Entry(self)
        self.relevant = tk.Button(self, text="Relevant", command = self.calculate1)
        self.not_relevant = tk.Button(self, text="Not Relevant", command=self.calculate2)
        self.output = tk.Label(self, text="")

        # lay the widgets out on the screen.
        self.prompt.pack(side="top", fill="x")
        # self.entry.pack(side="top", fill="x", padx=20)
        self.output.pack(side="top", fill="x", expand=True)
        self.not_relevant.pack(side="bottom")
        self.relevant.pack(side="bottom")


        self.tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                  filter={"$and": [{"crowdsourced": {"$exists": False}},
                                                                   {TWEET.SET_TO_FACTCHECK: {"$exists": False}},
                                                                   {TWEET.TOPICS: {"$exists":True}}]},
                                                  #                                                                   {TWEET.SET_TO_FACTCHECK,
                                                  projection={"text": 1}, sort=True, sort_field="retweet_count",
                                                  limit=500)
        self.current = self.tweets.next()
        self.bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
        self.bulk_count = 0
        self.prompt.configure(text=self.current["text"])

        # for tweet in tweets:

    def calculate1(self):
        try:

            self.db_connection.add_to_bulk_upsert(query={"_id": self.current["_id"]},
                                                  data={TWEET.SET_TO_FACTCHECK: True},
                                                  bulk_op=self.bulk_op)
            self.bulk_count += 1
            if self.bulk_count != 0 and self.bulk_count % 100 == 0:
                self.db_connection.end_bulk_upsert(bulk_op=self.bulk_op)
                self.bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)

            self.current = self.tweets.next()
            if self.current:
                self.prompt.configure(text=self.current['text'].encode('ascii', 'ignore'))

            else:
                if self.bulk_count != 0 and self.bulk_count % 100 == 0:
                    self.db_connection.end_bulk_upsert(bulk_op=self.bulk_op)
            # result = self.not_relevant.getboolean(False)

        except Exception as e:
            print e

        # set the output widget to have our result
        # self.output.configure(text=result)

    def calculate2(self):
        try:

            result = self.relevant.getboolean(True)
            self.db_connection.add_to_bulk_upsert(query={"_id": self.current["_id"]},
                                                  data={TWEET.SET_TO_FACTCHECK: False},
                                                  bulk_op=self.bulk_op)
            self.bulk_count += 1
            if self.bulk_count != 0 and self.bulk_count % 100 == 0:
                self.db_connection.end_bulk_upsert(bulk_op=self.bulk_op)
                self.bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)

            self.current = self.tweets.next()
            if self.current:
                self.prompt.configure(text=self.current['text'].encode('ascii', 'ignore'))

            else:
                if self.bulk_count != 0 and self.bulk_count % 100 == 0:
                    self.db_connection.end_bulk_upsert(bulk_op=self.bulk_op)

            # result = self.not_relevant.getboolean(False)

        except Exception as e:
            print e

        # set the output widget to have our result
        # self.output.configure(text=result)

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
    HumanComputeGUI(root).pack(fill="both", expand=True)
    root.mainloop()