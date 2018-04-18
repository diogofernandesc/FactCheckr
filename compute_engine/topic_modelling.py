# from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
# from sklearn.decomposition import NMF, LatentDirichletAllocation
# import re
# import numpy as np
# from db_engine import DBConnection
# from cons import DB
#
#
# def display_topics(model, feature_names, no_top_words):
#     for topic_idx, topic in enumerate(model.components_):
#         print "Topic %d:" % (topic_idx)
#         print " ".join([feature_names[i]
#                         for i in topic.argsort()[:-no_top_words - 1:-1]])
#
#
# def display_topics_extended(H, W, feature_names, documents, no_top_words, no_top_documents):
#     for topic_idx, topic in enumerate(H):
#         print "Topic %d:" % (topic_idx)
#         print " ".join([feature_names[i]
#                         for i in topic.argsort()[:-no_top_words - 1:-1]])
#         top_doc_indices = np.argsort( W[:,topic_idx] )[::-1][0:no_top_documents]
#         for doc_index in top_doc_indices:
#             print documents[doc_index]
#
#
# def update_mp_topics(db_connection, model_lda, model_nmf, feature_names_lda, feature_names_nmf, no_top_words):
#     total_lda_topics = []
#     total_nmf_topics = []
#     for topic_idx, topic in enumerate(model_lda.components_):
#         topic_keys = [feature_names_lda[i] for i in topic.argsort()[:-no_top_words - 1:-1]]
#         total_lda_topics.append(topic_keys)
#     mp = db_connection.find_and_update(collection=DB.MP_COLLECTION,
#         query={"twitter_handle": "@AdamAfriyie"},
#         update={"$set": {"topics_of_interest_lda": total_lda_topics}})
#
#     for topic_idx, topic in enumerate(model_nmf.components_):
#         topic_keys = [feature_names_nmf[i] for i in topic.argsort()[:-no_top_words - 1:-1]]
#         total_nmf_topics.append(topic_keys)
#     mp = db_connection.find_and_update(collection=DB.MP_COLLECTION,
#         query={"twitter_handle": "@AdamAfriyie"},
#         update={"$set": {"topics_of_interest_nmf": total_nmf_topics}})
#
#
# db_connection = DBConnection()
# data = db_connection.find_document(collection=DB.TWEET_COLLECTION,
#                                    filter={"author_handle": "@AdamAfriyie"},
#                                    projection={"text": 1})
#
# stopwords.txt = ["thx"]
# results = []
# for item in data:
#     item = re.sub(r"http\S+", "", item["text"])
#     item = re.sub(r"https\S+", "", item)
#     item = re.sub(r'\b\w{1,3}\b', '', item)
#     item = item.replace("&amp;", " ")
#
#     ' '.join(filter(lambda x: x.lower() not in stopwords.txt, item.split()))
#     # item = re.sub(r'^https?:\/\/.*[\r\n]*', '', item["text"])
#     # item = re.sub(r'^http?:\/\/.*[\r\n]*', '', item)
#     results.append(item)
#
# # LDA:
# no_features = 1000
# tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2, max_features=no_features, stop_words='english')
# tf = tf_vectorizer.fit_transform(results)
# tf_feature_names = tf_vectorizer.get_feature_names()
#
# # # NMF:
# tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, max_features=no_features, stop_words='english')
# tfidf = tfidf_vectorizer.fit_transform(results)
# tfidf_feature_names = tfidf_vectorizer.get_feature_names()
#
#
# no_topics = 15
#
# # Run NMF
# nmf = NMF(n_components=no_topics, max_iter=300, random_state=1, alpha=.1, l1_ratio=.7, init='nndsvd').fit(tfidf)
#
#
# lda = LatentDirichletAllocation(n_components=no_topics, max_iter=300, learning_method='online', learning_offset=0, random_state=0).fit(tf)
# # lda_model = LatentDirichletAllocation(n_components=no_topics, max_iter=75, learning_method='online',
# #                                       learning_offset=25., random_state=1).fit(tf)
#
# #
# # lda_W = lda_model.transform(tf)
# # lda_H = lda_model.components_
#
# no_top_words = 5
# no_top_documents = 4
#
# # no_topics = 20
# # no_top_words = 10
# # # Run LDA
# # lda = LatentDirichletAllocation(n_topics=no_topics,
# #                                 max_iter=500,
# #                                 learning_method='online',
# #                                 learning_offset=50.,
# #                                 random_state=1).fit(tf)
#
# # display_topics(nmf, tfidf_feature_names, no_top_words)
# # # display_topics(lda_H, lda_W, tf_feature_names, results, no_top_words, no_top_documents)
# # display_topics(lda, tf_feature_names, no_top_words)
#
# # mp = db_connection.find_and_update(collection=DB.MP_COLLECTION,
#                                    # filter={"author_handle": "@AdamAfriyie"},
#                                    # update={"$set": {"topics_of_interest": topics_of_interest}}
#
# update_mp_topics(db_connection=db_connection, model_lda=lda, model_nmf=nmf,
#                  feature_names_lda=tf_feature_names, feature_names_nmf=tfidf_feature_names,
#                  no_top_words=no_top_words)
#
#
#
#
#



import os
from collections import Counter

from gensim.corpora import Dictionary
from nltk.corpus import stopwords

from db_engine import DBConnection
from cons import DB
import re
from nltk.tokenize import RegexpTokenizer
from nltk.stem.wordnet import WordNetLemmatizer
from gensim.models import LdaModel, Phrases
from tweet_handler import TweetHandler
from gensim import corpora, models, similarities
from nltk.tokenize import word_tokenize


# class TopicModelling(TweetHandler):
#     def __init__(self):
#         self.db_connection = DBConnection()
#         self.tweets = self.get_clean(filter={"author_id":117777690})
#         self.tweets = self.tokenize(self.tweets)
#         self.tweets = self.lemmatize(self.tweets)
#         self.bigrams(self.tweets)
#         self.vectorize(self.tweets)
#         self.train()
#
#     def tokenize(self, tweets):
#         """
#         Tokenize tweets for computation
#         :return: Tokenized tweet list
#         """
#         # Split the documents into tokens.
#         tokenizer = RegexpTokenizer(r'\w+')
#         for idx in range(len(tweets)):
#             tweets[idx] = tweets[idx].lower()  # Convert to lowercase.
#             tweets[idx] = tokenizer.tokenize(tweets[idx])  # Split into words.
#
#         # Remove numbers, but not words that contain numbers.
#         docs = [[token for token in doc if not token.isnumeric()] for doc in tweets]
#
#         # Remove words that are only one character.
#         return [[token for token in doc if len(token) > 1] for doc in docs]
#
#     def lemmatize(self, tweets):
#         """
#         Lemmatize tweets
#         :param tweets: tweets to lemmatize
#         :return:
#         """
#         lemmatizer = WordNetLemmatizer()
#         return [[lemmatizer.lemmatize(token) for token in doc] for doc in tweets]
#
#     def bigrams(self, tweets):
#         """
#         Compute bigrams
#
#         :param tweets:
#         :return:
#         """
#         # Add bigrams and trigrams to docs (only ones that appear 20 times or more).
#         bigram = Phrases(tweets, min_count=20)
#         for idx in range(len(tweets)):
#             for token in bigram[tweets[idx]]:
#                 if '_' in token:
#                     # Token is a bigram, add to document.
#                     self.tweets[idx].append(token)
#
#     def vectorize(self, tweets):
#         """
#         Remove rare and common words and vectorize tweets
#         Remove words that appear in less than 20 documents or in more than 50% of the documents.
#         :param tweets:
#         :return:
#         """
#         self.dictionary = Dictionary(tweets)
#         self.dictionary.filter_extremes(no_below=10, no_above=0.5)
#         self.corpus = [self.dictionary.doc2bow(tweet) for tweet in tweets]
#
#     def train(self):
#         """
#         Train LDA model for tweets topic modelling
#         :param tweets:
#         :return:
#         """
#         # Set training parameters.
#         num_topics = 5
#         chunksize = 2000
#         passes = 50
#         iterations = 400
#         eval_every = None  # Don't evaluate model perplexity, takes too much time.
#
#         # Make a index to word dictionary.
#         temp = self.dictionary[0]
#         id2word = self.dictionary.id2token
#         self.model = LdaModel(corpus=self.corpus, id2word=id2word, chunksize=chunksize,
#                               alpha='auto', eta='auto', iterations=iterations, num_topics=num_topics,
#                               passes=passes, eval_every=eval_every)
#
#     def get_top_topics(self):
#         """
#         Get top topics for an MP
#         :return:
#         """
#         top_topics = self.model.top_topics(self.corpus, topn=5)
#         return top_topics





class TopicModel(object):
    def __init__(self):
        self.db_connection = DBConnection()

    def clean_tweet(self, tweet):
        regex_remove = "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|&amp;|amp|(\w+:\/\/\S+)|^RT|http.+?"
        tweet_text = re.sub(regex_remove, '', tweet["text"]).strip()
        tweet_id = tweet["_id"]

        stopword_list = []
        stopword_file = open('stopwords.txt', 'r')
        for line in stopword_file:
            stopword_list.append(line.strip())
        stopword_list = stopword_list + stopwords.words('english')
        stop_words = set(stopword_list)
        tweet_text = " ".join(word.lower() for word in tweet_text.split() if word.lower() not in stop_words)
        tweet["text"] = tweet_text
        return tweet

    def get_final_topics(self, topics):
        kw_list = []
        for topic_kws in topics:
            topic_kws = re.findall('"([^"]*)"', topic_kws[1])
            kw_list = kw_list + topic_kws
            # clean_topics.append(clean_topics)
        top_kws = [kw for kw, kw_count in Counter(kw_list).most_common(30)]
        print top_kws
            # pass

    def model(self, mp_id):
        '''
        Topic model by MP
        :return:
        '''
        tweet_docs = []
        tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                  filter={"author_id": mp_id}, projection={"text": 1})

        for tweet in tweets:
            tweet_docs.append(self.clean_tweet(tweet))


        # dictionary = gensim.corpora.Dictionary(gen_docs)
        # corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
        # tf_idf = gensim.models.TfidfModel(corpus)

        gen_docs = [[w.lower() for w in word_tokenize(tweet['text'].lower())] for tweet in tweet_docs]
        dictionary = corpora.Dictionary(gen_docs)
        # dictionary.save(os.path.join(TEMP_FOLDER, 'elon.dict'))  # store the dictionary, for future reference

        corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
        # corpora.MmCorpus.serialize()
        # corpora.MmCorpus.serialize(os.path.join(TEMP_FOLDER, 'elon.mm'), corpus)  # store to disk, for later use

        tfidf = models.TfidfModel(corpus)  # step 1 -- initialize a model
        corpus_tfidf = tfidf[corpus]

        total_topics = 5

        total_topic_aggregation = 5
        i = 0
        possible_topics = []
        while i < total_topic_aggregation:
            possible_topics = possible_topics + models.LdaModel(corpus,
                                                                id2word=dictionary,
                                                                num_topics=total_topics).show_topics(total_topics, 5)
            i += 1

        self.get_final_topics(topics=possible_topics)

        # topics1 = models.LdaModel(corpus, id2word=dictionary, num_topics=total_topics)
        # topics2 =
        # lda2 =models.LdaModel(corpus, id2word=dictionary, num_topics=total_topics)
        # corpus_lda = lda[corpus_tfidf]  # create a double wrapper over the original corpus: bow->tfidf->fold-in-lsi
        # topics =  lda.show_topics(total_topics, 5)
        # self.topics_to_list(topics)
        # print "----"
        # print lda2.show_topics(total_topics, 5)
        # print topics


if __name__ == "__main__":
    # topic_modelling = TopicModelling()
    tm = TopicModel()
    tm.model(mp_id=117777690)
    # topics = topic_modelling.get_top_topics()
    # print topics

