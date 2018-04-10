import gensim
from db_engine import DBConnection
from cons import DB
from nltk.tokenize import word_tokenize
'''
Determine the relevancy of a tweet for crowdsourcing based on several factors:
- Similarity to news articles (mentions of news articles, topics talked about)
- The importance of a news article
- Wikipedia trends for the day, week and month of the tweet
- Twitter trends for the day and week (month is too irrelevant for Twitter)
'''


class Relevancy(object):
    def __init__(self):
        self.db_connection = DBConnection()

    def create_similarity_model(self, timestamp, tweet):
        '''
        Given a timestamp, gets relevant:
         - News articles
         - Trends
        Builds the contents of these into similarity measure object
        :param timestamp:
        :return: similarity measure object to query tweets against
        '''

        documents = []
        articles_ingest = self.db_connection.find_document(collection=DB.NEWS_ARTICLES,
                                                    filter={"$and": [{"timestamp": {"$lt": timestamp}}, {"timestamp": {"$gt":1519569271}}]},
                                                    projection={"title": 1, "description": 1})

        twitter_trends_ingest = self.db_connection.find_document(collection=DB.TWITTER_TRENDS,
                                                          filter={"$and": [{"timestamp_epoch": {"$lt": timestamp}}, {"timestamp_epoch": {"$gt":1519569271}}]},
                                                          projection={"name": 1})

        wiki_trends_ingest = self.db_connection.find_document(collection=DB.WIKI_TRENDS,
                                                       filter={"$and": [{"epoch_timestamp": {"$lt": timestamp}}, {"epoch_timestamp": {"$gt":1519569271}}]},
                                                       projection={"name": 1})

        for article in articles_ingest:
            documents.append(article['description'])
            documents.append(article['title'])

        for trend in twitter_trends_ingest:
            documents.append(trend['name'])

        for trend in wiki_trends_ingest:
            documents.append(trend['name'])

        gen_docs = [[w.lower() for w in word_tokenize(text)] for text in documents]
        dictionary = gensim.corpora.Dictionary(gen_docs)
        corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
        tf_idf = gensim.models.TfidfModel(corpus)
        # sims = gensim.similarities.Similarity('gensim', tf_idf[corpus], num_features=len(dictionary))

        index = gensim.similarities.SparseMatrixSimilarity(tf_idf[corpus], num_features=len(dictionary))
        query_doc = [w.lower() for w in word_tokenize(tweet)]
        query_doc_bow = dictionary.doc2bow(query_doc)
        query_doc_tf_idf = tf_idf[query_doc_bow]

        sims = index[query_doc_tf_idf]
        print(list(enumerate(sims)))

        # print sims[query_doc_tf_idf]



rel = Relevancy()
tweet = rel.db_connection.find_document(collection=DB.TWEET_COLLECTION, filter={"_id": 965948087922552833},
                                        projection={"text": 1})

rel.create_similarity_model(1521988471, tweet=tweet[0]['text'])



