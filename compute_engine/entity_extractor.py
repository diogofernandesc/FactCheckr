import logging

import sys
sys.path.append("..")
from requests import ConnectionError
import twitter_ner_fork.NoisyNLP.models
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, KeywordsOptions, EntitiesOptions, RelationsOptions
from watson_developer_cloud.watson_service import WatsonApiException
import os
from db_engine import DBConnection
from cons import DB, TWEET
import re
from tweet_handler import TweetHandler
from nltk.corpus import stopwords
import nltk
import time
import logging
from rosette.api import API, DocumentParameters, RosetteException

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

from twitter_ner_fork.run_ner import TwitterNER
from twitter_ner_fork.twokenize import tokenizeRawTweetText


class EntityExtractor(TweetHandler):
    def __init__(self):
        super(EntityExtractor, self).__init__()
        self.nlu = NaturalLanguageUnderstandingV1(version='2017-02-27',
                                                  username=os.getenv('IBM_USER'), password=os.getenv('IBM_PASS'))
        self.rosette = API(user_key="331743f71a335b14c1c7a9f5498e65b1")
        # self.twitter_ner = TwitterNER()

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
                doc = {
                    "entity": entity['mention'].lower(),
                    "type": entity["type"],
                }
                if "confidence" in entity:
                    doc["certainty"] = entity["confidence"]
                    extracted_entities.append(doc)

                elif "linkingConfidence" in entity:
                    doc["certainty"] = entity["linkingConfidence"]
                    extracted_entities.append(doc)

            return extracted_entities
        except RosetteException as exception:
            warns = ['meaningful', 'Language']
            # if ['meaningful', 'Language'] not in exception.message:
            if not any(warn in exception.message for warn in warns):
                raise RosetteException(status=exception.status,
                                       message=exception.message,
                                       response_message=exception.response_message)


            else:
                return []



    def analyse_ner(self, tweet):
        tokens = tokenizeRawTweetText(tweet)
        entity_info = self.twitter_ner.get_entities(tokens)
        entities = []
        for entity in entity_info:
            index1 = entity[0]
            index2 = entity[1]
            en_type = entity[2]
            entities.append({
                "entity": " ".join(tokens[index1:index2]).lower(),
                "type": en_type
            })
        return entities

    def analyse(self, retweets=False):
        """
        :param since_epoch: timestamp from which to collect tweets
        :param retweets: Analyse recent tweets or not, default is no
        Extract keywords and entities from tweets
        :return:
        """
        collection = DB.RELEVANT_TWEET_COLLECTION
        if retweets:
            collection = DB.RETWEET_COLLECTION

        # Get tweets that have not been analysed yet
        # tweets = self.get_clean(collection=collection,
        #                         filter={"$and": [{"created_at_epoch": {"$gt": since_epoch}},
        #                                          {"created_at_epoch": {"$lt": 1523491200}},
        #                                          {"$or": [{"keywords": None}, {"entities": None}]}]})

        tweets = self.get_clean(collection=collection, filter={"$and": [{"keywords.certainty": {"$exists": False}},
                                                                        # 12th march
                                                                        {"created_at_epoch": {"$gt": 1520812800}}]})
        bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)

        count = 0
        try:
            # Tweets is a list of tuples=(tweet_id, tweet_text)
            for tweet in tweets:
                keywords = []
                entities = []
                try:
                    response = self.nlu.analyze(text=tweet[1], features=Features(keywords=KeywordsOptions(),
                                                                                 entities=EntitiesOptions()))
                except WatsonApiException:
                    response = []

                # ner_entities = self.analyse_ner(tweet=tweet[1])
                rosette_entities = self.analyse_rosette(tweet=tweet[1])
                entities = entities + rosette_entities

                if response:
                    for keyword in response['keywords']:
                        if " " in keyword['text'] and keyword['relevance'] < 0.4:
                            keywords.append({
                                "keyword": " ".join(keyword['text'].split()),
                                "certainty": keyword['relevance']
                            })
                            # keywords = keywords + (keyword['text'].split())
                        else:
                            keywords.append({
                                "keyword": keyword['text'],
                                "certainty": keyword['relevance']
                            })
                            # keywords.append(keyword['text'])

                    for entity in response['entities']:
                        updated_entity = False
                        for existing_entity in entities:
                            if existing_entity['entity'] == entity['text'].lower():
                                existing_entity['entity'] = existing_entity['entity'].title()

                                existing_entity['certainty'] = (existing_entity['certainty'] + entity['relevance']) / 2
                                updated_entity = True

                        if not updated_entity:
                            entities.append({
                                "entity": entity['text'],
                                "type": entity["type"],
                                "certainty": entity['relevance']
                            })

                        # Check there is not already an entity in the list of dicts
                        # if any(entity_data['entity'] == entity['text'].lower() for entity_data in entities):
                        #     entity = entity['text'].title()
                        #     entity_certainty =
                        #

                doc = {
                    TWEET.ENTITIES: entities,
                    TWEET.KEYWORDS: keywords
                }

                self.db_connection.add_to_bulk_upsert(query={"_id": tweet[0]}, data=doc, bulk_op=bulk_op)

                count += 1
                if count % 100 == 0:
                    logger.info("Extracted entities and keywords for %s tweets" % count)

            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)

        except RosetteException as exception:
            logger.warn("Rossete API exception: %s" % exception)
            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)


def main():
    while True:
        # 1514764800 = 1st of January 2018 00:00:00
        # ext.analyse(since_epoch=1520812800) #12th march 2018
        # ext.analyse(since_epoch=1514764800, retweets=True)
        ext.analyse()

        logger.info("Now sleeping entity/keyword extractor")
        time.sleep(60 * 60 * 26)  # Check every 26 hours (after tweet ingest)


if __name__ == "__main__":
    ext = EntityExtractor()
    try:
        main()
    except ConnectionError as e:
        logger.info("Restarting script due to %s" % e.message)
        main()



