import re
import nltk
import emoji
from datetime import datetime
from db_engine import DBConnection
from cons import DB


class FeatureExtractor(object):
    def __init__(self):
        self.db_connection = DBConnection()

    def get_tweet_features(self, tweets):
        '''
        Given a list of tweets, extracts the necessary features for this tweet for the classifier
        This includes a tweet's:
        - Number of characters
        - Number of words
        - Contains a question mark
        - Contains an exclamation mark
        - Are there multiple exclamation marks or question marks
        - Contains happy emoji(s)
        - Contains unhappy emoji(s)
        - Contains pronouns
        - No.of URLS
        - Contains popular domain top 100
        - Contains popular domain top 1000
        - Contains popular domain top 10000
        - Mentions user
        - Contains hashtag
        - Contains stock symbol e.g. $GOOGL
        - Day of the week in which tweet was made
        - No.of positive words
        - No.of negative words
        - Total final sentiment score
        - Relevance score from news
        - No.of entities extracted
        - Average certainty of entities extracted
        - No.of keywords extracted
        :param tweets: List of tweets to perform feature extraction
        :return:
        '''

        for tweet in tweets:
            text = tweet['text']
            timestamp = tweet['created_at_epoch']
            no_chars = len(re.sub(r"\s+", "", text))
            no_words = len(re.findall(r'\w+', text))
            contains_qm = "?" in text
            contains_em = "!" in text
            multiple_marks = text.count("?") > 1 or text.count("!") > 1
            happy_emoji = []

            # Pronoun extraction
            tokens = nltk.word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)

            # Extracting user mentions
            result = re.findall("(^|[^@\w])@(\w{1,15})", text)

            # Extracting stock symbols
            stock_result = re.findall("@([a-zA-Z0-9]{1,15})", text)

            day_of_week = datetime.fromtimestamp(timestamp).strftime("%A")

            # def extract_emojis(str):
            #     return ''.join(c for c in str if c in emoji.UNICODE_EMOJI)


ft = FeatureExtractor()
tweets = ft.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION, filter={"_id":957614547635965952})
ft.get_tweet_features(tweets=tweets)