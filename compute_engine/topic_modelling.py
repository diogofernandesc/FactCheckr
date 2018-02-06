from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation
import re
import numpy as np
from db_engine import DBConnection
from cons import DB


def display_topics(model, feature_names, no_top_words):
    for topic_idx, topic in enumerate(model.components_):
        print "Topic %d:" % (topic_idx)
        print " ".join([feature_names[i]
                        for i in topic.argsort()[:-no_top_words - 1:-1]])


def display_topics_extended(H, W, feature_names, documents, no_top_words, no_top_documents):
    for topic_idx, topic in enumerate(H):
        print "Topic %d:" % (topic_idx)
        print " ".join([feature_names[i]
                        for i in topic.argsort()[:-no_top_words - 1:-1]])
        top_doc_indices = np.argsort( W[:,topic_idx] )[::-1][0:no_top_documents]
        for doc_index in top_doc_indices:
            print documents[doc_index]


def update_mp_topics(db_connection, model_lda, model_nmf, feature_names_lda, feature_names_nmf, no_top_words):
    total_lda_topics = []
    total_nmf_topics = []
    for topic_idx, topic in enumerate(model_lda.components_):
        topic_keys = [feature_names_lda[i] for i in topic.argsort()[:-no_top_words - 1:-1]]
        total_lda_topics.append(topic_keys)
    mp = db_connection.find_and_update(collection=DB.MP_COLLECTION,
        query={"twitter_handle": "@AdamAfriyie"},
        update={"$set": {"topics_of_interest_lda": total_lda_topics}})

    for topic_idx, topic in enumerate(model_nmf.components_):
        topic_keys = [feature_names_nmf[i] for i in topic.argsort()[:-no_top_words - 1:-1]]
        total_nmf_topics.append(topic_keys)
    mp = db_connection.find_and_update(collection=DB.MP_COLLECTION,
        query={"twitter_handle": "@AdamAfriyie"},
        update={"$set": {"topics_of_interest_nmf": total_nmf_topics}})


db_connection = DBConnection()
data = db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                   filter={"author_handle": "@AdamAfriyie"},
                                   projection={"text": 1})

stopwords = ["thx"]
results = []
for item in data:
    item = re.sub(r"http\S+", "", item["text"])
    item = re.sub(r"https\S+", "", item)
    item = re.sub(r'\b\w{1,3}\b', '', item)
    item = item.replace("&amp;", " ")

    ' '.join(filter(lambda x: x.lower() not in stopwords, item.split()))
    # item = re.sub(r'^https?:\/\/.*[\r\n]*', '', item["text"])
    # item = re.sub(r'^http?:\/\/.*[\r\n]*', '', item)
    results.append(item)

# LDA:
no_features = 1000
tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2, max_features=no_features, stop_words='english')
tf = tf_vectorizer.fit_transform(results)
tf_feature_names = tf_vectorizer.get_feature_names()

# # NMF:
tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, max_features=no_features, stop_words='english')
tfidf = tfidf_vectorizer.fit_transform(results)
tfidf_feature_names = tfidf_vectorizer.get_feature_names()


no_topics = 15

# Run NMF
nmf = NMF(n_components=no_topics, max_iter=300, random_state=1, alpha=.1, l1_ratio=.7, init='nndsvd').fit(tfidf)


lda = LatentDirichletAllocation(n_components=no_topics, max_iter=300, learning_method='online', learning_offset=0, random_state=0).fit(tf)
# lda_model = LatentDirichletAllocation(n_components=no_topics, max_iter=75, learning_method='online',
#                                       learning_offset=25., random_state=1).fit(tf)

#
# lda_W = lda_model.transform(tf)
# lda_H = lda_model.components_

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

# display_topics(nmf, tfidf_feature_names, no_top_words)
# # display_topics(lda_H, lda_W, tf_feature_names, results, no_top_words, no_top_documents)
# display_topics(lda, tf_feature_names, no_top_words)

# mp = db_connection.find_and_update(collection=DB.MP_COLLECTION,
                                   # filter={"author_handle": "@AdamAfriyie"},
                                   # update={"$set": {"topics_of_interest": topics_of_interest}}

update_mp_topics(db_connection=db_connection, model_lda=lda, model_nmf=nmf,
                 feature_names_lda=tf_feature_names, feature_names_nmf=tfidf_feature_names,
                 no_top_words=no_top_words)

