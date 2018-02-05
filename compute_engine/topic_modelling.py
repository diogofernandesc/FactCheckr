from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
import re
import numpy as np
from db_engine import DBConnection
from cons import DB
# from sklearn.datasets import fetch_20newsgroups
#
# dataset = fetch_20newsgroups(shuffle=True, random_state=1, remove=('headers', 'footers', 'quotes'))
# documents = dataset.data
# print documents


db_connection = DBConnection()
data = db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                   filter={"author_handle": "@AdamAfriyie"},
                                   projection={"text": 1})

results = []
for item in data:
    item = re.sub(r"http\S+", "", item["text"])
    item = re.sub(r"https\S+", "", item)
    item = item.replace("&amp;", " ")
    # item = re.sub(r'^https?:\/\/.*[\r\n]*', '', item["text"])
    # item = re.sub(r'^http?:\/\/.*[\r\n]*', '', item)
    results.append(item)

no_features = 10000
tf_vectorizer = CountVectorizer(max_df=0.90, min_df=0, max_features=no_features, stop_words='english')
tf = tf_vectorizer.fit_transform(results)
tf_feature_names = tf_vectorizer.get_feature_names()


# def display_topics(model, feature_names, no_top_words):
#     for topic_idx, topic in enumerate(model.components_):
#         print "Topic %d:" % (topic_idx)
#         print " ".join([feature_names[i]
#                         for i in topic.argsort()[:-no_top_words - 1:-1]])

def display_topics(H, W, feature_names, documents, no_top_words, no_top_documents):
    for topic_idx, topic in enumerate(H):
        print "Topic %d:" % (topic_idx)
        print " ".join([feature_names[i]
                        for i in topic.argsort()[:-no_top_words - 1:-1]])
        top_doc_indices = np.argsort( W[:,topic_idx] )[::-1][0:no_top_documents]
        for doc_index in top_doc_indices:
            print documents[doc_index]


no_topics = 5
lda_model = LatentDirichletAllocation(n_components=no_topics, max_iter=25, learning_method='online', learning_offset=50.,random_state=1).fit(tf)
lda_W = lda_model.transform(tf)
lda_H = lda_model.components_

no_top_words = 5
no_top_documents = 4

# no_topics = 20
# no_top_words = 10
# # Run LDA
# lda = LatentDirichletAllocation(n_topics=no_topics,
#                                 max_iter=500,
#                                 learning_method='online',
#                                 learning_offset=50.,
#                                 random_state=1).fit(tf)

display_topics(lda_H, lda_W, tf_feature_names, results, no_top_words, no_top_documents)
# display_topics(lda, tf_feature_names, no_top_words)
