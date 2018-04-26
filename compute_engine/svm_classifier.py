import operator

from db_engine import DBConnection
from sklearn import datasets, preprocessing
from sklearn import svm
import numpy as np
from cons import DB, TWEET, TOPIC, MP

class Classifier(object):
    def __init__(self):
        self.db_connection = DBConnection()
        self.iris = datasets.load_iris()
        self.digits = datasets.load_digits()
        self.classifier = svm.SVC(probability=True)

    def train(self, train_data, train_target):
        '''
        Trains SVM classifier based on the feature set acquired in feature_extractor
        Normalises data for optimal results
        Gets class decision and probabilistic result
        :return:
        '''
        clean_train_data = []

        # Cleaning of data in preparation for training
        for tweet in train_data:
            tweet_block = [
                tweet[TWEET.CHARACTER_COUNT],
                tweet[TWEET.WORD_COUNT],
                int(tweet[TWEET.CONTAINS_QM]),
                int(tweet[TWEET.CONTAINS_EM]),
                int(tweet[TWEET.CONTAINS_MULTIPLE_MARKS]),
                tweet[TWEET.FRACTION_CAPITALISED],
                int(tweet[TWEET.CONTAINS_HAPPY_EMOJI]),
                int(tweet[TWEET.CONTAINS_SAD_EMOJI]),
                int(tweet[TWEET.CONTAINS_HAPPY_EMOTICON]),
                int(tweet[TWEET.CONTAINS_SAD_EMOTICON]),
                int(tweet[TWEET.CONTAINS_PRONOUNS]),
                int(tweet[TWEET.CONTAINS_DOMAIN_TOP10]),
                int(tweet[TWEET.CONTAINS_DOMAIN_TOP30]),
                int(tweet[TWEET.CONTAINS_DOMAIN_TOP50]),
                int(tweet[TWEET.MENTIONS_USER]),
                int(tweet[TWEET.CONTAINS_STOCK_SYMBOL]),
                tweet[TWEET.PUBLISH_WEEKDAY],
                tweet[TWEET.POSITIVE_WORD_COUNT],
                tweet[TWEET.NEGATIVE_WORD_COUNT],
                tweet[TWEET.SENTIMENT_SCORE],
                tweet[TWEET.AVERAGE_ENTITY_CERTAINTY],
                tweet[TWEET.AVERAGE_KEYWORD_CERTAINTY],
                tweet[TWEET.ENTITIES_COUNT],
                tweet[TWEET.KEYWORDS_COUNT],
                tweet[TWEET.RELEVANCY_DAY],
                tweet[TWEET.RELEVANCY_WEEK],
                tweet[TWEET.RELEVANCY_TWO_WEEKS],
                int(tweet[TWEET.CONTAINS_FIGURES]),
                tweet[TWEET.FRAC_NOT_IN_DICT]
            ]

            mp_data = self.db_connection.find_document(collection=DB.MP_COLLECTION,
                                                       filter={"_id": tweet[TWEET.AUTHOR_ID]},
                                                       projection={MP.FOLLOWERS_COUNT: 1,
                                                                   MP.FRIENDS_COUNT: 1,
                                                                   MP.TWEET_COUNT: 1,
                                                                   MP.IS_VERIFIED: 1,
                                                                   MP.AVERAGE_NO_RETWEETS: 1,
                                                                   MP.AVERAGE_NO_FAVOURITES: 1,
                                                                   MP.ACCOUNT_DAYS: 1})
            for mp in mp_data:
                mp_block = [
                    mp[MP.FOLLOWERS_COUNT],
                    mp[MP.FRIENDS_COUNT],
                    mp[MP.TWEET_COUNT],
                    int(mp[MP.IS_VERIFIED]),
                    mp[MP.AVERAGE_NO_RETWEETS],
                    mp[MP.AVERAGE_NO_FAVOURITES],
                    mp[MP.ACCOUNT_DAYS]
                ]
                break

            top_topic = max(tweet[TWEET.TOPICS], key=lambda x: x[TOPIC.IDENTIFIED_AS_TOPIC])
            topics = self.db_connection.find_document(collection=DB.RELEVANT_TOPICS,
                                             filter={"_id": top_topic["_id"]})

            for topic in topics:
                topic_block = [
                    topic[TOPIC.TWEET_COUNT],
                    topic[TOPIC.TWEET_AVERAGE_LENGTH],
                    topic[TOPIC.FRAC_CONTAINING_QM],
                    topic[TOPIC.FRAC_CONTAINING_EM],
                    topic[TOPIC.FRAC_CONTAINING_MULTIPLE_MARKS],
                    topic[TOPIC.FRAC_CONTAINING_HAPPY_EMOTICON],
                    topic[TOPIC.FRAC_CONTAINING_SAD_EMOTICON],
                    topic[TOPIC.FRAC_CONTAINING_HAPPY_EMOJI],
                    topic[TOPIC.FRAC_CONTAINING_SAD_EMOJI],
                    topic[TOPIC.FRAC_CONTAINING_PRONOUNS],
                    topic[TOPIC.FRAC_CONTAINING_FIGURES],
                    topic[TOPIC.FRAC_CONTAINING_UPPERCASE],
                    topic[TOPIC.FRAC_CONTAINING_URL],
                    topic[TOPIC.FRAC_CONTAINING_USER_MENTION],
                    topic[TOPIC.FRAC_CONTAINING_HASHTAGS],
                    topic[TOPIC.FRAC_CONTAINING_STOCK_SYMBOLS],
                    topic[TOPIC.AVERAGE_SENTIMENT_SCORE],
                    topic[TOPIC.FRAC_CONTAINING_POSITIVE_SENTIMENT],
                    topic[TOPIC.FRAC_CONTAINING_NEGATIVE_SENTIMENT],
                    topic[TOPIC.FRAC_CONTAINING_DOMAIN10],
                    topic[TOPIC.FRAC_CONTAINING_DOMAIN30],
                    topic[TOPIC.FRAC_CONTAINING_DOMAIN50],
                    topic[TOPIC.DISTINCT_URLS_COUNT],
                    topic[TOPIC.FRAC_CONTAINING_MOST_VISITED_URL],
                    topic[TOPIC.DISTINCT_HASHTAG_COUNT],
                    topic[TOPIC.FRAC_CONTAINING_MOST_USED_HASHTAG],
                    topic[TOPIC.DISTINCT_USER_MENTION_COUNT],
                    topic[TOPIC.FRAC_CONTAINING_MOST_MENTIONED_USER],
                    topic[TOPIC.DISTINCT_TWEET_AUTHOR_COUNT],
                    topic[TOPIC.FRAC_CONTAINING_TOP_AUTHOR],
                    topic[TOPIC.AVERAGE_AUTHOR_TWITTER_LIFE],
                    topic[TOPIC.AVERAGE_AUTHOR_TWEET_COUNT],
                    topic[TOPIC.AVERAGE_AUTHOR_FOLLOWER_COUNT],
                    topic[TOPIC.AVERAGE_AUTHOR_FRIEND_COUNT],
                    topic[TOPIC.FRAC_FROM_VERIFIED],
                    topic[TOPIC.AVERAGE_DAY_RELEVANCE],
                    topic[TOPIC.AVERAGE_WEEK_RELEVANCE],
                    topic[TOPIC.AVERAGE_2WEEK_RELEVANCE],
                    topic[TOPIC.AVERAGE_WORDS_NOT_IN_DICT]
                ]
                break

            data_block = tweet_block + mp_block + topic_block
            clean_train_data.append(data_block)

        X = np.array(clean_train_data)
        X = preprocessing.scale(X)
        self.classifier.fit(X=X, y=train_target)


        coef = self.classifier.coef_  # here the weights of the features will be stored

    def predict(self, target_data):
        '''
        Get predictions for the target data
        :param target_data: array of feature sets for each tweet
        :return:
        '''
        predictions = self.classifier.predict(target_data)
        class_probabilities = self.classifier.predict_proba(target_data)


if __name__ == "__main__":
    clf = Classifier()
    tweets = clf.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                             filter={"$and":[{TWEET.SET_TO_FACTCHECK: True},
                                                             {TWEET.LABEL: {"$exists": False}},
                                                             {TWEET.TOPICS:{"$exists": True}}]})

    print tweets.count()
    tweets = list(tweets)
    labels = [tweet[TWEET.CONTAINS_FIGURES] for tweet in tweets]
    clf.train(train_data=tweets, train_target=labels)
    clf.start()

