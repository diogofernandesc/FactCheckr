# coding=utf-8
from __future__ import unicode_literals
from __future__ import division
import calendar
import os
import re
import nltk
import emoji
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from db_engine import DBConnection
from ingest_engine.twitter_ingest import Twitter
from cons import DB, EMOJI_HAPPY, EMOJI_UNHAPPY, CREDS, MP, DOMAIN, TWEET, WEEKDAY
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
                                                  username="b90a4616-36a2-447a-941f-256419b8f3e4",
                                                  password="t0BCpLI8fzSA")

        self.twitter = Twitter(os.environ.get(CREDS.TWITTER_KEY),
                                  os.environ.get(CREDS.TWITTER_SECRET),
                                  os.environ.get(CREDS.TWITTER_TOKEN),
                                  os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
                                  self.db_connection)
        self.session = requests.session()

    def convert_weekday(self, weekday):
        week_dict = {
            "Monday": WEEKDAY.MONDAY,
            "Tuesday": WEEKDAY.TUESDAY,
            "Wednesday": WEEKDAY.WEDNESDAY,
            "Thursday": WEEKDAY.THURSDAY,
            "Friday": WEEKDAY.FRIDAY,
            "Saturday": WEEKDAY.SATURDAY,
            "Sunday": WEEKDAY.SUNDAY
        }

        return week_dict.get(weekday)

    def get_top_websites(self):
        domains_to_insert = []
        rank = 0
        with open("top_news_domains", "rb") as f:
            for line in f:
                line = line.decode("utf8").strip()
                if "Website" in line:
                    rank += 1
                    domain_info = {
                        DOMAIN.URL: line.split(" ")[1],
                        DOMAIN.RANK: rank
                    }
                    domains_to_insert.append(domain_info)

        f.close()
        self.db_connection.bulk_insert(data=domains_to_insert, collection=DB.TOP_NEWS_DOMAINS)

    def get_tweet_features(self, tweets):
        '''
        Given a list of tweets, extracts the necessary features for this tweet for the classifier
        This includes a tweet's:
        - Number of characters
        - Number of words
        - Contains a question mark
        - Contains an exclamation mark
        - Fraction of capital letters
        - Are there multiple exclamation marks or question marks
        - Contains happy emoji(s)
        - Contains unhappy emoji(s)
        - Contains happy emoticon
        - Contains unhappy emoticon
        - Contains pronouns
        - No.of URLS
        - Contains popular domain top 10
        - Contains popular domain top 30
        - Contains popular domain top 50
        - Mentions user
        - Contains hashtag
        - Contains stock symbol e.g. $GOOGL
        - Day of the week in which tweet was made: - Monday = 1 ...... Sunday = 7
        - No.of positive words
        - No.of negative words
        - Total final sentiment score
        - Relevance score from news: day, week, 2weeks
        - No.of entities extracted
        - No.of keywords extracted
        - Average certainty of entities extracted
        - Average relevance of keywords extracted
        :param tweets: List of tweets to perform feature extraction
        :return:
        '''

        bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
        for tweet in tweets:
            tweet = {
                "_id" : 956217250092077056,
                "retweet_count" : 21,
                "favourites_count" : 20,
                "links": [
                    "https://t.co/QAcTz1HCEh.",
                    "https://t.co/RDNcqDKPwb",
                    "http://www.bbc.co.uk/news/uk-43840710"
                ],
                "url" : "https://t.co/Tv74ZcbGdR",
                "text" : "Marvellous news @GregHands. UK Businesses bad should be confident about continuity and stability in the short term and optimistic about the work @tradegovuk are doing to open us up to the world in the longer term https://t.co/c91Vt3bs2Y",
                "created_at" : "2018-01-24T17:28:52.000+0000",
                "author_handle" : "@AdamAfriyie",
                "last_updated" : "2018-02-26T18:36:00.202+0000",
                "author_id" : 22031058,
                "created_at_epoch" : 1516814932,
                "html" : "<blockquote class=\"twitter-tweet\"><p lang=\"en\" dir=\"ltr\">With the Pound at its highest value since the referendum and the employment rate the highest ever recorded, now is the time to be confident about leaving the Single Market <a href=\"https://t.co/Tv74ZcbGdR\">https://t.co/Tv74ZcbGdR</a> <a href=\"https://twitter.com/ExpressSeries?ref_src=twsrc%5Etfw\">@ExpressSeries</a> <a href=\"https://twitter.com/windsorobserver?ref_src=twsrc%5Etfw\">@windsorobserver</a> <a href=\"https://twitter.com/bracknellnews?ref_src=twsrc%5Etfw\">@bracknellnews</a></p>&mdash; Adam Afriyie (@AdamAfriyie) <a href=\"https://twitter.com/AdamAfriyie/status/956217250092077056?ref_src=twsrc%5Etfw\">January 24, 2018</a></blockquote>\n<script async src=\"https://platform.twitter.com/widgets.js\" charset=\"utf-8\"></script>\n",
                "entities" : [
                    {
                        "certainty" : 0.99900001,
                        "type" : "TITLE",
                        "entity" : "governor"
                    },
                    {
                        "certainty" : 0.6645000050000001,
                        "type" : "PERSON",
                        "entity" : "Virginia"
                    },
                    {
                        "certainty" : 0.2188269,
                        "type" : "LOCATION",
                        "entity" : "uk"
                    },
                    {
                        "certainty" : 0.6645000050000001,
                        "type" : "ORGANIZATION",
                        "entity" : "Commonwealth Virginia"
                    }
                ],
                "keywords" : [
                    {
                        "certainty" : 0.944038,
                        "keyword" : "Governor Virginia UK"
                    },
                    {
                        "certainty" : 0.873367,
                        "keyword" : "links Commonwealth Virginia"
                    },
                    {
                        "certainty" : 0.64328,
                        "keyword" : "Outstanding meeting"
                    }
                ],
                "relevancy_day" : 0.014215469360351562,
                "relevancy_week" : 0.013840186409652233,
                "relevancy_2weeks" : 0.013843044638633728,
                "relevancy_month" : 0.013843044638633728
            }

            text = re.sub(r'http\S+', '', tweet['text']) # Remove links
            capitalised = sum(1 for c in text if c.isupper())
            text = text.lower()
            timestamp = tweet['created_at_epoch']
            no_chars = len(re.sub(r"\s+", "", text))
            no_words = len(re.findall(r'\w+', text))
            capitalised = capitalised / no_chars
            contains_qm = "?" in text
            contains_em = "!" in text
            multiple_marks = text.count("?") > 1 or text.count("!") > 1
            # happy_emoji = []

            # Pronoun extraction
            tokens = nltk.word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            has_personal_pronoun = False
            for tag in pos_tags:
                has_personal_pronoun = tag[0] in ['PRP', 'PRP$']
                if has_personal_pronoun:
                    break

            # Extracting user mentions
            user_mentions = re.findall("(^|[^@\w])@(\w{1,15})", text)
            user_mentions = [mention[1] for mention in user_mentions]
            # Extracting stock symbols
            stock_result = re.findall("$([a-zA-Z0-9]{1,15})", text)

            day_of_week = datetime.fromtimestamp(timestamp).strftime("%A")

            # Extracting emoticons
            happy_emoticons = """
            :‑) :) :-] :] :-3 :3 :-> :> 8-) 8) :-} :} :o) :c) :^) =] =) :‑D :D 8‑D 8D x‑D xD X‑D XD =D =3 B^D :-)) :'‑) 
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
            sad_emoji_count = len([c for c in text.split() if c in EMOJI_UNHAPPY])

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


            # Domain extraction
            top10 = False
            top30 = False
            top50 = False
            for url in tweet[TWEET.LINKS]:
                url = requests.head(url, allow_redirects=True).url
                url = url.split("://")[1]
                if "www" in url:
                    url = url.split("www.")[1]

                if "/" in url:
                    url = url.split("/")[0]

                if len(url.split('.')[0]) > 1:
                    # regexp = re.compile("/.*%s.*/" % url, re.IGNORECASE)
                    regexp = "/.*%s.*/" % url
                    match = self.db_connection.find_document(collection=DB.TOP_NEWS_DOMAINS,
                                                             filter={"url": {"$regex": url}})

                    for domain in match:
                        rank = domain["rank"]
                        top10 = rank <= 10
                        top30 = 11 <= rank <= 30
                        top50 = 31 <= rank <= 50

            # Certainty extraction
            entity_certainty = 0
            keyword_certainty = 0
            for entity in tweet[TWEET.ENTITIES]:
                entity_certainty += entity['certainty']

            for keyword in tweet[TWEET.KEYWORDS]:
                keyword_certainty += keyword['certainty']


            # Sentiment extraction

            try:
                sentiment_response = self.nlu.analyze(text=text, features=Features(sentiment=SentimentOptions()))
                sentiment_score += sentiment_response['sentiment']['document']['score']
            except WatsonApiException as e:
                logger.warn(e.message)
                sentiment_score = 0

            doc = {
                TWEET.CHARACTER_COUNT: no_chars,
                TWEET.WORD_COUNT: no_words,
                TWEET.CONTAINS_QM: contains_qm,
                TWEET.CONTAINS_EM: contains_em,
                TWEET.CONTAINS_MULTIPLE_MARKS: multiple_marks,
                TWEET.FRACTION_CAPITALISED: capitalised,
                TWEET.CONTAINS_HAPPY_EMOJI: happy_emoji_count > 0,
                TWEET.CONTAINS_SAD_EMOJI: sad_emoji_count > 0,
                TWEET.CONTAINS_HAPPY_EMOTICON: len(happy_emoticon_count) > 0,
                TWEET.CONTAINS_SAD_EMOTICON: len(sad_emoticon_count) > 0,
                TWEET.CONTAINS_PRONOUNS: has_personal_pronoun,
                TWEET.MENTIONED_USERS: user_mentions,
                TWEET.MENTIONS_USER: len(user_mentions) > 0,
                TWEET.CONTAINS_STOCK_SYMBOL: len(stock_result) > 0,
                TWEET.PUBLISH_WEEKDAY: self.convert_weekday(day_of_week),
                TWEET.POSITIVE_WORD_COUNT: pos_word_count,
                TWEET.NEGATIVE_WORD_COUNT: neg_word_count,
                TWEET.SENTIMENT_SCORE: sentiment_score,
                TWEET.AVERAGE_ENTITY_CERTAINTY: entity_certainty / len(tweet[TWEET.ENTITIES]),
                TWEET.AVERAGE_KEYWORD_CERTAINTY: keyword_certainty / len(tweet[TWEET.KEYWORDS]),
                TWEET.ENTITIES_COUNT: len(tweet[TWEET.ENTITIES]),
                TWEET.KEYWORDS_COUNT: len(tweet[TWEET.KEYWORDS]),
                TWEET.CONTAINS_DOMAIN_TOP10: top10,
                TWEET.CONTAINS_DOMAIN_TOP30: top30,
                TWEET.CONTAINS_DOMAIN_TOP50: top50

                # TWEET.CONTAINS_DOMAIN_TOP10:
            }

            self.db_connection.add_to_bulk_upsert(query={"_id": tweet["_id"]},
                                                  data=doc, bulk_op=bulk_op)

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
        - Average number of retweets
        - Average number of favourites

        :param users:
        :return:
        '''

        for user in users:
            tweet_info = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                          filter={"author_handle": user["twitter_handle"]},
                                                          projection={"retweet_count": 1, "favourites_count": 1}
                                                          )
            cursor_count = tweet_info.count()
            total_retweets = 0
            total_favourites = 0
            for tweet in tweet_info:
                total_favourites += tweet["favourites_count"]
                total_retweets += tweet["retweet_count"]

            user_data = self.twitter.api.GetUser(user_id=user["_id"])
            created_at = datetime.strptime(user_data.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            final_date = datetime(year=2018, month=4, day=15)
            days_since = (final_date - created_at).days
            timestamp = calendar.timegm(created_at.timetuple())

            if user_data.status:
                doc = {
                    MP.IS_VERIFIED: user_data.verified,
                    MP.FRIENDS_COUNT: user_data.friends_count,
                    MP.AVERAGE_NO_FAVOURITES: total_favourites / cursor_count,
                    MP.AVERAGE_NO_RETWEETS: total_retweets / cursor_count,
                    MP.NON_EMPTY_DESCRIPTION: len(user_data.description) > 0,
                    MP.ACCOUNT_DAYS: days_since
                }
                print user_data

    def get_topic_features(self, topics):
        '''
        Extract features for a given topic, including:
        - amount of tweets
        - Average length
        - Fraction containing questioning mark
        - Fraction containing exclamation mark
        - Fraction containing multiple question marks/multiple exclamation marks
        - Fraction containing happy emoticon, sad emoticon, happy emoji, sad emoji
        - Fraction containing pronouns
        - Fraction containing 30% of characters uppercased
        - Fraction containing a URL
        - Fraction containing a user mention
        - Fraction containing hashtags
        - Fraction containing stock symbols
        - Average sentiment score
        - Fraction containing positive sentiment score
        - Fraction containing negative sentiment score
        - Fraction containing popular domain top 10
        - Fraction containing popular domain top 30
        - Fraction containing popular domain top 50
        - Number of distinct URLs
        - Fraction containing most visited URL
        - Number of distinct short URLs
        - Number of distinct hashtags
        - Fraction containing most used hashtag
        - Number of distinct users mentioned
        - Fraction containing most mentioned user
        - Number of distinct tweet authors
        - Fraction of tweets by most frequent author
        - Author average twitter life
        - Author average amount of tweets
        - Author average amount of followers
        - Author average amount of friends
        - Fraction of tweets from verified users
        - Fraction with authors with description
        :param topics:
        :return:
        '''


if __name__ == "__main__":
    ft = FeatureExtractor()
    # ft.get_top_websites()
    tweets = ft.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION, filter={})
    # users = ft.db_connection.find_document(collection=DB.MP_COLLECTION, filter={})
    # ft.get_user_features(users=users)
    ft.get_tweet_features(tweets=tweets)