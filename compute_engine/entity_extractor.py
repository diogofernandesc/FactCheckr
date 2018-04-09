from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, KeywordsOptions, EntitiesOptions, RelationsOptions
import os
from db_engine import DBConnection
from cons import DB
import re
from tweet_handler import TweetHandler
from nltk.corpus import stopwords
import nltk
import time
import logging
from rosette.api import API, DocumentParameters, RosetteException

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

class EntityExtractor(TweetHandler):
    def __init__(self):
        super(EntityExtractor, self).__init__()
        self.nlu = NaturalLanguageUnderstandingV1(version='2017-02-27',
                                                  username=os.getenv('IBM_USER'), password=os.getenv('IBM_PASS'))
        self.rosette = API(user_key=os.getenv("ROSETTE_API_KEY"))

    def get_clean(self, filter={}, limit=1000, tweet=None):
        """
        Override
        Get tweets for specific MP and clean tweet
        :param filter: Filter for selecting tweets to clean
        :return: Clean tweets for a given MP
        """
        clean_tweets = []
        if not tweet:
            tweets = self.db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                                      filter=filter,
                                                      projection={"text": 1},
                                                      limit=limit)

        else:
            tweets = [tweet]

        for tweet in tweets:
            regex_remove = "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|&amp;|amp|(\w+:\/\/\S+)|^RT|http.+?"
            tweet_text = re.sub(regex_remove, '', tweet["text"]).strip()
            tweet_id = tweet["_id"]

            stopword_list = []
            stopword_file = open('stopwords.txt', 'r')
            for line in stopword_file:
                stopword_list.append(line.strip())
            stopword_list = stopword_list + stopwords.words('english')
            stop_words = set(stopword_list)

            tweet_text = " ".join(word for word in tweet_text.split() if word not in stop_words)
            clean_tweets.append((tweet_id, tweet_text))

        return clean_tweets

    def analyse_rosette(self, tweet):
        params = DocumentParameters()
        params["content"] = tweet[1]
        params["genre"] = "social-media"

        extracted_entities = []
        try:
            entities = self.rosette.entities(params)
            for entity in entities['entities']:
                extracted_entities.append({
                    "entity": entity['mention'],
                    "type": entity["type"]

                })
            return extracted_entities

        except RosetteException as exception:
            logger.warn("Rossete API exception: %s" % exception)

    def analyse(self, tweets):
        """
        Extract keywords and entities from tweets
        :return:
        """

        # Tweets is a list of tuples=(tweet_id, tweet_text)
        for tweet in tweets:
            keywords = []
            entities = []
            response = self.nlu.analyze(text=tweet[1], features=Features(keywords=KeywordsOptions(),
                                                                         entities=EntitiesOptions()))
            rosette_entities = self.analyse_rosette(tweet=tweet)
            entities = entities + rosette_entities

            for keyword in response['keywords']:
                keywords.append(keyword['text'])

            for entity in response['entities']:
                entities.append({
                    "entity": entity['text'],
                    "type": entity["type"]
                })


            print tweet[0]
            result_tweet = self.db_connection.find_and_update(collection=DB.TWEET_COLLECTION,
                                                              query={"_id": tweet[0]},
                                                              update={"$set": {"keywords": keywords,
                                                                               "entities": entities}})

            print result_tweet


if __name__ == "__main__":
    ext = EntityExtractor()

    while True:
        # Get tweets that have not been analysed yet
        tweets = ext.get_clean(filter={"$or": [{"keywords": None}, {"entities": None}]})
        # tweets = ext.db_connection.find_document(collection=DB.TWEET_COLLECTION,
        #                                           filter={"$or": [{"keywords": None}, {"entities": None}]},
        #                                           projection={"text": 1},
        #                                           limit=10)
        if tweets:
            ext.analyse(tweets=tweets)

        time.sleep(60 * 60 * 2)  # Check every 2 hours



