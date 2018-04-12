import gensim
import time
from cons import CREDS
from ingest_engine.twitter_ingest import Twitter
import math
import os
from db_engine import DBConnection
from cons import DB, TIME_INTERVAL, RELEVANCY_INTERVAL
from nltk.tokenize import word_tokenize
import numpy as np
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import re

'''
Determine the relevancy of a tweet for crowdsourcing based on several factors:
- Similarity to news articles (mentions of news articles, topics talked about)
- The importance of a news article (Basis for relevance0
- Wikipedia trends for the day, week and month of the tweet (10% relevance each)
- Twitter trends for the day and week (month is too irrelevant for Twitter) (10% relevance)
'''


class Relevancy(object):
    def __init__(self):
        self.db_connection = DBConnection()
        self.twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
                                   os.environ.get(CREDS.TWITTER_SECRET),
                                   os.environ.get(CREDS.TWITTER_TOKEN),
                                   os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
                                   self.db_connection)

    def cleaner(self, tweets):
        '''
        Remove tweets that are too insignificant to classify for relevance score e.g. tweets with one word
        :param tweets: list of tweets to clean
        :return:
        '''
        for tweet in tweets:
            try:
                if tweet['text']:
                    tweet_data = self.twitter_api.get_status(tweet_id=tweet["_id"])
                    lang = detect(tweet['text'])
                    if tweet_data.in_reply_to_status_id:  # It's a reply, not worth fact-checking
                        self.db_connection.delete_tweet(tweet_id=tweet["_id"])

                    elif lang != 'en':
                        self.db_connection.delete_tweet(tweet_id=tweet["_id"])

                    elif len(re.findall(r'\w+', tweet['text'])) <= 10:
                        self.db_connection.delete_tweet(tweet_id=tweet["_id"])

                    elif tweet['text'].count('@') > 4:
                        self.db_connection.delete_tweet(tweet_id=tweet["_id"])

                    elif tweet['text'].count('#') > 4:
                        self.db_connection.delete_tweet(tweet_id=tweet["_id"])

            except LangDetectException as e:
                print e
                self.db_connection.delete_tweet(tweet['text'])

    def get_prediction_model(self, timestamp, time_interval):
        '''
        Given a timestamp, gets relevant:
         - News articles
         - Trends
        Builds the contents of these into similarity measure object
        :param tweet: Tweet to analyse
        :param timestamp: Timestamp to analyse from
        :param time_interval: Interval of time for which to create the similarity
        :return: similarity measure object to query tweets against
        '''

        start_timestamp = timestamp - time_interval

        articles = []
        articles_ingest = self.db_connection.find_document(collection=DB.NEWS_ARTICLES,
                                                           filter={"$and": [{"timestamp": {"$gt": start_timestamp}},
                                                                            {"timestamp": {"$lt": timestamp}}]},
                                                           projection={"title": 1, "description": 1})

        if articles_ingest.count() > 0:
            for article in articles_ingest:
                if 'description' in article:
                    if article['description']:
                        articles.append(article['description'])

                if 'title' in article:
                    if article['title']:
                        articles.append(article['title'])

            gen_docs = [[w.lower() for w in word_tokenize(text)] for text in articles]
            dictionary = gensim.corpora.Dictionary(gen_docs)
            corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
            tf_idf = gensim.models.TfidfModel(corpus)
            # sims = gensim.similarities.Similarity('gensim', tf_idf[corpus], num_features=len(dictionary))

            index = gensim.similarities.SparseMatrixSimilarity(tf_idf[corpus], num_features=len(dictionary))

            return [index, dictionary, tf_idf]

        else:
            return None


    def calculate_relevance(self, tweets, timestamp, time_interval):
        start_timestamp = timestamp - time_interval

        model = self.get_prediction_model(timestamp=timestamp, time_interval=time_interval)
        if model:
            twitter_trends_ingest = self.db_connection.find_document(collection=DB.TWITTER_TRENDS,
                                                                     filter={"$and": [
                                                                         {"timestamp_epoch": {"$gt": start_timestamp}},
                                                                         {"timestamp_epoch": {"$lt": timestamp}}]},
                                                                     projection={"name": 1})

            wiki_trends_ingest = self.db_connection.find_document(collection=DB.WIKI_TRENDS,
                                                                  filter={"$and": [
                                                                      {"epoch_timestamp": {"$gt": start_timestamp}},
                                                                      {"epoch_timestamp": {"$lt": timestamp}}]},
                                                                  projection={"name": 1})

            for tweet in tweets:
                query_doc = [w.lower() for w in word_tokenize(tweet['text'])]
                query_doc_bow = model[1].doc2bow(query_doc)
                query_doc_tf_idf = model[2][query_doc_bow]

                sims = model[0][query_doc_tf_idf]
                relevance = sims[sims != 0].mean()

                if not math.isnan(relevance):
                    twitter_trends = []
                    wiki_trends = []

                    for trend in twitter_trends_ingest:
                        twitter_trends.append(trend['name'])

                    for trend in wiki_trends_ingest:
                        wiki_trends.append(trend['name'])

                    for trend in twitter_trends:
                        if trend in tweet:
                            relevance += (0.1 * relevance)  # 10% relevance booster for each trend

                    for trend in wiki_trends:
                        if trend in tweet:
                            relevance += (0.1 * relevance)  # 10% relevance booster for each trend

                    relevance = float(relevance)

                    if time_interval == TIME_INTERVAL.DAY:
                        self.db_connection.update_tweet(tweet_id=tweet["_id"], update={RELEVANCY_INTERVAL.DAY: relevance})

                    elif time_interval == TIME_INTERVAL.WEEK:
                        self.db_connection.update_tweet(tweet_id=tweet["_id"], update={RELEVANCY_INTERVAL.WEEK: relevance})

                    elif time_interval == TIME_INTERVAL.WEEK * 2:
                        self.db_connection.update_tweet(tweet_id=tweet["_id"], update={RELEVANCY_INTERVAL.TWO_WEEKS: relevance})

                    elif time_interval == TIME_INTERVAL.MONTH:
                        self.db_connection.update_tweet(tweet_id=tweet["_id"], update={RELEVANCY_INTERVAL.MONTH: relevance})

                else:
                    continue


def main():
    rel = Relevancy()

    # 11th Jan 2018
    initial_timestamp = 1515715200
    timestamp = initial_timestamp
    end_timestamp = time.time()

    tweets = rel.db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                             filter={"relevancy_week": {"$exists": True}},
                                             projection={"text": 1})

    if tweets.count() > 0:
        rel.cleaner(tweets)

    # while timestamp <= end_timestamp:
    #     period_timestamp = timestamp + TIME_INTERVAL.DAY
    #     # tweets = rel.db_connection.find_document(collection=DB.TWEET_COLLECTION,
    #     #                                          filter={"$and": [
    #     #                                              {"created_at_epoch": {"$lt": period_timestamp}},
    #     #                                              {"created_at_epoch": {"$gt": timestamp}},
    #     #                                              {"relevancy_week": {"$exists": True}}
    #     #                                          ]},
    #     #                                          projection={"text": 1})
    #
    #
    #
    #     # if tweets.count() > 0:
    #     #     rel.cleaner(tweets)
    #         # rel.calculate_relevance(tweets=tweets, timestamp=timestamp, time_interval=TIME_INTERVAL.MONTH)
    #
    #     timestamp = period_timestamp


# rel = Relevancy()
# tweet = rel.db_connection.find_document(collection=DB.TWEET_COLLECTION, filter={"_id": 965948087922552833},
#                                         projection={"text": 1})

main()
# rel.calculate_relevance(tweet=tweet[0], timestamp=1521988471, time_interval=TIME_INTERVAL.WEEK)



