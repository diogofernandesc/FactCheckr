import operator

from sklearn.grid_search import GridSearchCV

from db_engine import DBConnection
from sklearn import datasets, preprocessing
from sklearn import svm
import numpy as np
from cons import DB, TWEET, TOPIC, MP
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from sklearn.metrics import classification_report
from matplotlib import pyplot as plt
from matplotlib import rcParams

class Classifier(object):
    def __init__(self):
        self.db_connection = DBConnection()
        # self.iris = datasets.load_iris()
        # self.digits = datasets.load_digits()
        # self.classifier = svm.SVC(probability=True, kernel='linear')
        self.classifier = svm.SVC(probability=True, kernel='linear', C=1, gamma=1)
        self.clean_train_data = []
        self.classifier_predictions = None
        self.gold_results = None
        Cs = [0.001, 0.01, 0.1, 1, 10]
        gammas = [0.001, 0.01, 0.1, 1]
        self.coef = None
        self.features_names = [
            "tweet_%s" % TWEET.CHARACTER_COUNT,
            "tweet_%s" % TWEET.WORD_COUNT,
            "tweet_%s" % TWEET.CONTAINS_QM,
            "tweet_%s" % TWEET.CONTAINS_EM,
            "tweet_%s" % TWEET.CONTAINS_MULTIPLE_MARKS,
            "tweet_%s" % TWEET.FRACTION_CAPITALISED,
            "tweet_%s" % TWEET.CONTAINS_HAPPY_EMOJI,
            "tweet_%s" % TWEET.CONTAINS_SAD_EMOJI,
            "tweet_%s" % TWEET.CONTAINS_HAPPY_EMOTICON,
            "tweet_%s" % TWEET.CONTAINS_SAD_EMOTICON,
            "tweet_%s" % TWEET.CONTAINS_PRONOUNS,
            "tweet_%s" % TWEET.CONTAINS_DOMAIN_TOP10,
            "tweet_%s" % TWEET.CONTAINS_DOMAIN_TOP30,
            "tweet_%s" % TWEET.CONTAINS_DOMAIN_TOP50,
            "tweet_%s" % TWEET.MENTIONS_USER,
            "tweet_%s" % TWEET.CONTAINS_STOCK_SYMBOL,
            "tweet_%s" % TWEET.PUBLISH_WEEKDAY,
            "tweet_%s" % TWEET.POSITIVE_WORD_COUNT,
            "tweet_%s" % TWEET.NEGATIVE_WORD_COUNT,
            "tweet_%s" % TWEET.SENTIMENT_SCORE,
            "tweet_%s" % TWEET.AVERAGE_ENTITY_CERTAINTY,
            "tweet_%s" % TWEET.AVERAGE_KEYWORD_CERTAINTY,
            "tweet_%s" % TWEET.ENTITIES_COUNT,
            "tweet_%s" % TWEET.KEYWORDS_COUNT,
            "tweet_%s" % TWEET.RELEVANCY_DAY,
            "tweet_%s" % TWEET.RELEVANCY_WEEK,
            "tweet_%s" % TWEET.RELEVANCY_TWO_WEEKS,
            "tweet_%s" % TWEET.CONTAINS_FIGURES,
            "tweet_%s" % TWEET.FRAC_NOT_IN_DICT,
            "mp_%s" % MP.FOLLOWERS_COUNT,
            "mp_%s" % MP.FRIENDS_COUNT,
            "mp_%s" % MP.TWEET_COUNT,
            "mp_%s" % MP.IS_VERIFIED,
            "mp_%s" % MP.AVERAGE_NO_RETWEETS,
            "mp_%s" % MP.AVERAGE_NO_FAVOURITES,
            "mp_%s" % MP.ACCOUNT_DAYS,
            "topic_%s" % TOPIC.TWEET_COUNT,
            "topic_%s" % TOPIC.TWEET_AVERAGE_LENGTH,
            "topic_%s" % TOPIC.FRAC_CONTAINING_QM,
            "topic_%s" % TOPIC.FRAC_CONTAINING_EM,
            "topic_%s" % TOPIC.FRAC_CONTAINING_MULTIPLE_MARKS,
            "topic_%s" % TOPIC.FRAC_CONTAINING_HAPPY_EMOTICON,
            "topic_%s" % TOPIC.FRAC_CONTAINING_SAD_EMOTICON,
            "topic_%s" % TOPIC.FRAC_CONTAINING_HAPPY_EMOJI,
            "topic_%s" % TOPIC.FRAC_CONTAINING_SAD_EMOJI,
            "topic_%s" % TOPIC.FRAC_CONTAINING_PRONOUNS,
            "topic_%s" % TOPIC.FRAC_CONTAINING_FIGURES,
            "topic_%s" % TOPIC.FRAC_CONTAINING_UPPERCASE,
            "topic_%s" % TOPIC.FRAC_CONTAINING_URL,
            "topic_%s" % TOPIC.FRAC_CONTAINING_USER_MENTION,
            "topic_%s" % TOPIC.FRAC_CONTAINING_HASHTAGS,
            "topic_%s" % TOPIC.FRAC_CONTAINING_STOCK_SYMBOLS,
            "topic_%s" % TOPIC.AVERAGE_SENTIMENT_SCORE,
            "topic_%s" % TOPIC.FRAC_CONTAINING_POSITIVE_SENTIMENT,
            "topic_%s" % TOPIC.FRAC_CONTAINING_NEGATIVE_SENTIMENT,
            "topic_%s" % TOPIC.FRAC_CONTAINING_DOMAIN10,
            "topic_%s" % TOPIC.FRAC_CONTAINING_DOMAIN30,
            "topic_%s" % TOPIC.FRAC_CONTAINING_DOMAIN50,
            "topic_%s" % TOPIC.DISTINCT_URLS_COUNT,
            "topic_%s" % TOPIC.FRAC_CONTAINING_MOST_VISITED_URL,
            "topic_%s" % TOPIC.DISTINCT_HASHTAG_COUNT,
            "topic_%s" % TOPIC.FRAC_CONTAINING_MOST_USED_HASHTAG,
            "topic_%s" % TOPIC.DISTINCT_USER_MENTION_COUNT,
            "topic_%s" % TOPIC.FRAC_CONTAINING_MOST_MENTIONED_USER,
            "topic_%s" % TOPIC.DISTINCT_TWEET_AUTHOR_COUNT,
            "topic_%s" % TOPIC.FRAC_CONTAINING_TOP_AUTHOR,
            "topic_%s" % TOPIC.AVERAGE_AUTHOR_TWITTER_LIFE,
            "topic_%s" % TOPIC.AVERAGE_AUTHOR_TWEET_COUNT,
            "topic_%s" % TOPIC.AVERAGE_AUTHOR_FOLLOWER_COUNT,
            "topic_%s" % TOPIC.AVERAGE_AUTHOR_FRIEND_COUNT,
            "topic_%s" % TOPIC.FRAC_FROM_VERIFIED,
            "topic_%s" % TOPIC.AVERAGE_DAY_RELEVANCE,
            "topic_%s" % TOPIC.AVERAGE_WEEK_RELEVANCE,
            "topic_%s" % TOPIC.AVERAGE_2WEEK_RELEVANCE,
            "topic_%s" % TOPIC.AVERAGE_WORDS_NOT_IN_DICT
        ]



    def train(self, train_data, train_target):
        '''
        Trains SVM classifier based on the feature set acquired in feature_extractor
        Normalises data for optimal results
        Gets class decision and probabilistic result
        :return:
        '''
        # self.clean_train_data = []

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
            self.clean_train_data.append(data_block)

        X = np.array(self.clean_train_data)
        X = preprocessing.scale(X)
        # self.get_best_hyperparameters(X=X[:-60], y=train_target)
        # self.classifier.fit(X=X[:-60], y=train_target)
        self.classifier.fit(X=X[:-150], y=train_target)
        self.coef = self.classifier.coef_  # here the weights of the features will be stored


        self.get_feature_importance(self.classifier, feature_names=self.features_names, top_features=10)


        return X

    def predict(self, target_data):
        '''
        Get predictions for the target data
        :param target_data: array of feature sets for each tweet
        :return:
        '''
        predictions = self.classifier.predict(target_data)
        self.classifier_predictions = predictions.tolist()
        # class_probabilities = self.classifier.predict_proba(target_data)
        # print predictions
        # print class_probabilities

    def evaluate_classifier(self):
        target_names = ["false", "true"]
        # labeler1 = [2, 0, 2, 2, 0, 1]
        # labeler2 = [0, 0, 2, 2, 0, 2]
        print "predictions - true: %s" % self.classifier_predictions.count(1)
        print "predictions - false: %s" % self.classifier_predictions.count(0)
        print "ground truth - true: %s" % self.gold_results.count(1)
        print "ground truth - false: %s" % self.gold_results.count(0)
        kappa_score = cohen_kappa_score(self.classifier_predictions, self.gold_results)
        print ("kappa score: %s" % kappa_score)
        print(classification_report(self.gold_results, self.classifier_predictions, target_names=target_names))
        tn, fp, fn, tp = confusion_matrix(self.gold_results, self.classifier_predictions).ravel()
        print (tn, fp, fn, tp)


    def get_best_hyperparameters(self, X, y):
        Cs = [0.001, 0.01, 0.1, 1, 10]
        gammas = [0.001, 0.01, 0.1, 1]
        param_grid = {'C': Cs, 'gamma': gammas}
        grid_search = GridSearchCV(svm.SVC(kernel='linear'), param_grid, cv=25)
        grid_search.fit(X, y)
        grid_search.best_params_
        print grid_search.best_params_

    def get_feature_importance(self, classifier, feature_names,top_features=20):
        rcParams.update({'figure.autolayout': True})
        # imp = self.coef
        # imp, names = zip(*sorted(zip(imp, self.features_names)))
        # plt.barh(range(len(names)), imp, align='center')
        # plt.yticks(range(len(names)), names)
        # plt.show()
        coef = classifier.coef_.ravel()
        top_positive_coefficients = np.argsort(coef)[-top_features:]
        top_negative_coefficients = np.argsort(coef)[:top_features]
        top_coefficients = np.hstack([top_negative_coefficients, top_positive_coefficients])
        # create plot
        plt.figure(figsize=(10, 10))
        colors = ["red" if c < 0 else "green" for c in coef[top_coefficients]]
        plt.bar(np.arange(2 * top_features), coef[top_coefficients], color=colors)
        feature_names = np.array(feature_names)
        plt.xticks(np.arange(0, 2 * top_features), feature_names[top_coefficients], rotation=60, ha="right")
        # plt.xticks(np.arange(0, 1 + 2 * top_features), feature_names[top_coefficients], rotation=90)
        plt.ylabel("Feature coefficient")
        plt.xlabel("Feature name")
        plt.show()




    def get_ground_truth_set(self):
        tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                  filter={"$and":[{TWEET.AGGREGATE_LABEL:{"$exists": False}},
                                                                  {TWEET.TOPICS: {"$exists": True}},
                                                                  {TWEET.ENTITIES_COUNT: {"$gt": 0}},
                                                                  {TWEET.SET_TO_FACTCHECK: True}]},
                                                  projection={"text": 1})

        print tweets.count()
        total_count = 0
        for tweet in tweets:
            print tweet
            print "-------------"
            verdict = raw_input("Is the tweet true?\n")
            verdict = int("y" in verdict)
            self.db_connection.find_and_update(collection=DB.RELEVANT_TWEET_COLLECTION, query={"_id": tweet["_id"]},
                                               update={"$set": {TWEET.AGGREGATE_LABEL: verdict, TWEET.GOLDEN: True}})

            total_count += 1


if __name__ == "__main__":
    clf = Classifier()
    # clf.get_ground_truth_set()
    tweets = clf.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                             filter={"$and":[{TWEET.SET_TO_FACTCHECK: True},
                                                             {TWEET.TOPICS:{"$exists": True}},
                                                             {TWEET.AGGREGATE_LABEL: {"$exists": True}},
                                                             {TWEET.AGGREGATE_LABEL: {"$in": [1,0]}}]})

    gold_standard = clf.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                    filter={"golden":True})
    # gold_standard_true = clf.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
    #                                                 filter={"$and":[{"golden":True}, {TWEET.AGGREGATE_LABEL: 1}]},
    #                                                      limit=30)
    #
    # gold_standard_false = clf.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
    #                                                      filter={
    #                                                          "$and": [{"golden": True}, {TWEET.AGGREGATE_LABEL: 0}]},
    #                                                      limit=30)

    clf.gold_results = [x[TWEET.AGGREGATE_LABEL] for x in gold_standard]
    # clf.gold_results = [x[TWEET.AGGREGATE_LABEL] for x in gold_standard_true]
    # clf.gold_results = clf.gold_results + [x[TWEET.AGGREGATE_LABEL] for x in gold_standard_false]
    # not_crowdsourced = clf.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
    #                                                    filter={"$and": [{TWEET.SET_TO_FACTCHECK: True},
    #                                                                     {TWEET.TOPICS:{"$exists": True}},
    #                                                                     {TWEET.AGGREGATE_LABEL: {"$exists": False}}]},
    #                                                    limit=2)
    # not_crowdsourced = clf.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                       # filter={"_id": 960409744962936832})

    print len(clf.gold_results)
    print tweets.count()
    # extra_tweet = not_crowdsourced.next()
    # print extra_tweet['text']
    tweets = list(tweets)
    gold_standard = list(gold_standard)
    # gold_standard = list(gold_standard_true) + list(gold_standard_false)
    data = tweets + gold_standard
    # tweets.append(extra_tweet)
    # labels = [tweet[TWEET.AGGREGATE_LABEL] for tweet in data[:-60]]
    labels = [tweet[TWEET.AGGREGATE_LABEL] for tweet in data[:-150]]
    print len(labels)
    print len(tweets)
    scaled_data = clf.train(train_data=data, train_target=labels)
    # clf.predict(target_data=scaled_data[-60:])
    clf.predict(target_data=scaled_data[-150:])
    clf.evaluate_classifier()
    # clf.start()

