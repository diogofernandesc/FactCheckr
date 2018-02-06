from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, KeywordsOptions, EntitiesOptions, RelationsOptions
import os
from db_engine import DBConnection
from cons import DB


class EntityExtractor(object):
    def __init__(self):
        self.db_connection = DBConnection()
        self.nlu = NaturalLanguageUnderstandingV1(version='2017-02-27',
                                                  username=os.getenv('IBM_USER'), password=os.getenv('IBM_PASS'))
        self.db_connection.apply_field_to_all(field="keywords", value=None, collection=DB.TWEET_COLLECTION)
        self.db_connection.apply_field_to_all(field="entities", value=None, collection=DB.TWEET_COLLECTION)

    def analyse(self):
        for tweet in self.db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                                      filter={"author_handle": "@AdamAfriyie"},
                                                      projection={"text": 1}):

            keywords = []
            entities = []

            response = self.nlu.analyze(text=tweet["text"], features=Features(keywords=KeywordsOptions(),
                                                                     entities=EntitiesOptions(),
                                                                     relations=RelationsOptions()))
            for keyword in response['keywords']:
                keywords.append(keyword['text'])

            for entity in response['entities']:
                entities.append(entity['text'])

            result_tweet = self.db_connection.find_and_update(collection=DB.TWEET_COLLECTION,
                                                              query={"_id": tweet["_id"]},
                                                              update={"$set": {"keywords": keywords,
                                                                               "entities": entities}})


ext = EntityExtractor()
ext.analyse()