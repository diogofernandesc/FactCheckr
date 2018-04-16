# coding=utf-8
from __future__ import unicode_literals
import os
import re
import nltk
import emoji
import logging
from datetime import datetime
from db_engine import DBConnection
from cons import DB, EMOJI_HAPPY, EMOJI_UNHAPPY
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, SentimentOptions
from watson_developer_cloud.watson_service import WatsonApiException

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)

class FeatureExtractor(object):
    def __init__(self):
        self.db_connection = DBConnection()
        self.sid = SentimentIntensityAnalyzer()
        self.nlu = NaturalLanguageUnderstandingV1(version='2017-02-27',
                                                  username=os.getenv('IBM_USER'), password=os.getenv('IBM_PASS'))

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
        - Contains happy emoticon
        - Contains unhappy emoticon
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
        - No.of keywords extracted
        - Average certainty of entities extracted
        - Average relevance of keywords extracted
        :param tweets: List of tweets to perform feature extraction
        :return:
        '''

        for tweet in tweets:
            tweet = {
                "_id" : 956217250092077056,
                "retweet_count" : 21,
                "favourites_count" : 20,
                "url" : "https://t.co/Tv74ZcbGdR",
                "text" : "Marvellous news @GregHands. UK Businesses bad should be confident about continuity and stability in the short term and optimistic about the work @tradegovuk are doing to open us up to the world in the longer term https://t.co/c91Vt3bs2Y",
                "created_at" : "2018-01-24T17:28:52.000+0000",
                "author_handle" : "@AdamAfriyie",
                "last_updated" : "2018-02-26T18:36:00.202+0000",
                "author_id" : 22031058,
                "created_at_epoch" : 1516814932,
                "html" : "<blockquote class=\"twitter-tweet\"><p lang=\"en\" dir=\"ltr\">With the Pound at its highest value since the referendum and the employment rate the highest ever recorded, now is the time to be confident about leaving the Single Market <a href=\"https://t.co/Tv74ZcbGdR\">https://t.co/Tv74ZcbGdR</a> <a href=\"https://twitter.com/ExpressSeries?ref_src=twsrc%5Etfw\">@ExpressSeries</a> <a href=\"https://twitter.com/windsorobserver?ref_src=twsrc%5Etfw\">@windsorobserver</a> <a href=\"https://twitter.com/bracknellnews?ref_src=twsrc%5Etfw\">@bracknellnews</a></p>&mdash; Adam Afriyie (@AdamAfriyie) <a href=\"https://twitter.com/AdamAfriyie/status/956217250092077056?ref_src=twsrc%5Etfw\">January 24, 2018</a></blockquote>\n<script async src=\"https://platform.twitter.com/widgets.js\" charset=\"utf-8\"></script>\n",
                "entities" : [

                ],
                "keywords" : [
                    "Pound value referendum",
                    "employment rate",
                    "Single",
                    "Market"
                ],
                "relevancy_day" : 0.014215469360351562,
                "relevancy_week" : 0.013840186409652233,
                "relevancy_2weeks" : 0.013843044638633728,
                "relevancy_month" : 0.013843044638633728
            }

            text = re.sub(r'http\S+', '', tweet['text']) # Remove links
            text = text.lower()
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
            has_personal_pronoun = False
            for tag in pos_tags:
                has_personal_pronoun = tag[0] in ['PRP', 'PRP$']
                if has_personal_pronoun:
                    break

            # Extracting user mentions
            result = re.findall("(^|[^@\w])@(\w{1,15})", text)

            # Extracting stock symbols
            stock_result = re.findall("$([a-zA-Z0-9]{1,15})", text)

            day_of_week = datetime.fromtimestamp(timestamp).strftime("%A")

            # Extracting emoticons
            happy_emoticons = """
            :‑) :)	:-] :] :-3 :3 :-> :> 8-) 8)	:-} :} :o) :c) :^) =] =) :‑D :D	8‑D 8D x‑D xD X‑D XD =D =3 B^D :-)) :'‑) 
            :') :‑P :P :‑p :p =p >:P
            """.split()

            sad_emoticons = """
            :‑( :( :‑c :c :‑< :< :‑[ :[ :-|| >:[ :{	:@ >:( :'‑( :'( D‑': D:< D: D8 D; D= DX 
            :‑/ :/ :‑. >:\ >:/ :\ =/ =\	:L =L :S
            """.split()

            happy_emoticon_pattern = "|".join(map(re.escape, happy_emoticons))
            sad_emoticon_pattern = "|".join(map(re.escape, sad_emoticons))

            happy_emoticon_count = re.findall(happy_emoticon_pattern, text)
            sad_emoticon_count = re.findall(sad_emoticon_pattern, text)

            # Extracting emojis
            happy_emoji_count = len([c for c in text.split() if c in EMOJI_HAPPY])
            unhappy_emoji_count = len([c for c in text.split() if c in EMOJI_UNHAPPY])

            # Extracting sentiment score and its components

            sentiment_score = 0
            pos_word_count = 0
            neg_word_count = 0

            for word in text.split():
                with open('positive_words.txt') as positive_file:
                    if word in positive_file.read().split():
                        pos_word_count += 1

                    else:
                        positive_file.close()
                        with open('negative_words.txt') as negative_file:
                            if word in negative_file.read().split():
                                neg_word_count += 1


            try:
                sentiment_response = self.nlu.analyze(text=text, features=Features(sentiment=SentimentOptions()))
                sentiment_score += sentiment_response['sentiment']['document']['score']
            except WatsonApiException as e:
                logger.warn(e.message)

    def get_user_features(self, users):
        '''
        Given a list of users, extracts the necessary features for this user for the classifier
        The feature list includes:
        - Amount of days until now since user created account
        - Number of tweets
        - Number of followers
        - Number of followees
        - Is verified (1 if verified)
        - Has non empty description
        - Has homepage URL
        - Average number of retweets
        - Average number of favourites
        
        :param users:
        :return:
        '''



if __name__ == "__main__":
    ft = FeatureExtractor()
    tweets = ft.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION, filter={})
    ft.get_tweet_features(tweets=tweets)