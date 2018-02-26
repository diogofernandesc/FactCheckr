from db_engine import DBConnection
import re
from nltk.corpus import stopwords
from cons import DB


class TweetHandler(object):
    def __init__(self):
        self.db_connection = DBConnection()

    def get_clean(self, filter):
        """
        Get tweets for specific MP and clean tweet
        :param filter: Filter for selecting tweets to clean
        :return: Clean tweets for a given MP
        """
        tweets = self.db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                                  filter=filter,
                                                  projection={"text": 1})

        stopword_list = []
        stopword_file = open('stopwords.txt', 'r')
        for line in stopword_file:
            stopword_list.append(line.strip())
        stopword_list = stopword_list + stopwords.words('english')
        stop_words = set(stopword_list)
        tweets = map(lambda x: x["text"].lower(), tweets)  # Combine list into just text content

        regex_remove = "(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|&amp;|amp|(\w+:\/\/\S+)|^RT|http.+?"
        tweets = [re.sub(regex_remove, '', tweet).strip() for tweet in tweets]
        clean_tweets = []
        # Stop word removal from tweet
        for tweet in tweets:
            clean_tweets.append(" ".join(word for word in tweet.split() if word not in stop_words))

        return clean_tweets