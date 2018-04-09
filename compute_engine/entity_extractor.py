import logging

from requests import ConnectionError
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

    def get_clean(self, filter={}, limit=4000, tweet=None, collection=DB.TWEET_COLLECTION):
        """
        Override
        Get tweets for specific MP and clean tweet
        :param filter: Filter for selecting tweets to clean
        :return: Clean tweets for a given MP
        """
        clean_tweets = []
        if not tweet:
            tweets = self.db_connection.find_document(collection=collection,
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
        params["content"] = tweet
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


    def analyse(self, since_epoch, retweets=False):
        """
        :param since_epoch: timestamp from which to collect tweets
        :param retweets: Analyse recent tweets or not, default is no
        Extract keywords and entities from tweets
        :return:
        """
        collection = DB.TWEET_COLLECTION
        if retweets:
            collection = DB.RETWEET_COLLECTION

        # Get tweets that have not been analysed yet
        tweets = self.get_clean(collection=collection,
                                filter={"$and": [{"created_at_epoch": {"$gt": since_epoch}},
                                                 {"$or": [{"keywords": None}, {"entities": None}]}]})

        count = 0
        
        # Tweets is a list of tuples=(tweet_id, tweet_text)
        for tweet in tweets:
            keywords = []
            entities = []
            response = self.nlu.analyze(text=tweet[1], features=Features(keywords=KeywordsOptions(),
                                                                         entities=EntitiesOptions()))

            rosette_entities = self.analyse_rosette(tweet=tweet[1])
            entities = entities + rosette_entities

            for keyword in response['keywords']:
                if " " in keyword['text'] and keyword['relevance'] < 0.4:
                    keywords = keywords + (keyword['text'].split())
                else:
                    keywords.append(keyword['text'])

            for entity in response['entities']:
                entities.append({
                    "entity": entity['text'],
                    "type": entity["type"]
                })

            result_tweet = self.db_connection.find_and_update(collection=collection,
                                                              query={"_id": tweet[0]},
                                                              update={"$set": {"keywords": keywords,
                                                                               "entities": entities}})

            count += 1
            if count % 100 == 0:
                logger.info("Extracted entities and keywords for %s tweets" % count)


def main():
    while True:
        # 1514764800 = 1st of January 2018 00:00:00
        # ext.analyse(since_epoch=1514764800)
        ext.analyse(since_epoch=1514764800, retweets=True)

        logger.info("Now sleeping entity/keyword extractor")
        time.sleep(60 * 60 * 26)  # Check every 26 hours (after tweet ingest)


if __name__ == "__main__":
    ext = EntityExtractor()
    try:
        main()
    except ConnectionError as e:
        logger.info("Restarting script due to %s" % e.message)
        main()



