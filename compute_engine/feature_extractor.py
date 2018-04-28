# coding=utf-8
from __future__ import unicode_literals
from __future__ import division
import calendar
import os
import re
import threading
import urllib2
from collections import Counter
import multiprocessing
from multiprocessing.pool import ThreadPool
import time
import grequests as grequests
import nltk
import emoji
import logging
from datetime import datetime
from pymongo.errors import InvalidOperation
import operator
import requests
from bs4 import BeautifulSoup
from requests.exceptions import ConnectionError, TooManyRedirects
from db_engine import DBConnection
from ingest_engine.twitter_ingest import Twitter
from cons import DB, EMOJI_HAPPY, EMOJI_UNHAPPY, CREDS, MP, DOMAIN, TWEET, WEEKDAY, TOPIC
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, SentimentOptions
from watson_developer_cloud.watson_service import WatsonApiException
import enchant

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)


def exception_handler(request, exception):
    print exception

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
        self.resolved_urls = []
        # self.session = requests.session()

    def get_extra_features(self, tweets):
        '''
        Gets extra features such as whether tweet contains figures and percentage of words not in dictionary
        :param tweets:
        :return:
        '''
        english_dict = enchant.Dict("en_GB")
        bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
        bulk_count = 0
        for tweet in tweets:
            not_english = 0
            text = re.sub(r"http\S+", "", tweet['text'])
            figures = re.findall("-?\d+", text)
            no_words = len(re.findall(r'\w+', text))
            has_figures = len(figures) > 0
            clean_text = ''.join([i for i in text if not i.isdigit()])
            clean_text = re.sub(r'[^\w]', ' ', clean_text)
            for word in clean_text.split():
                if not english_dict.check(word):
                    not_english += 1

            doc = {
                TWEET.CONTAINS_FIGURES: has_figures,
                TWEET.FRAC_NOT_IN_DICT: not_english / no_words
            }

            self.db_connection.add_to_bulk_upsert(query={"_id": tweet["_id"]}, data=doc, bulk_op=bulk_op)
            bulk_count += 1
            if bulk_count % 100 == 0:
                self.db_connection.end_bulk_upsert(bulk_op=bulk_op)
                bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
                logger.info("Pushing 100 extra featured tweets to DB")

        if bulk_count > 0 and bulk_count % 100 != 0:
            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)
            logger.info("Final DB push for tweets with extra features")




    def chunks(self, l, n):
        """Yield successive n-sized chunks from l."""
        for i in range(0, len(l), n):
            yield l[i:i + n]

    def resolve_url(self, urls):
        db_connection = DBConnection()
        url_list = []
        try:
            r = requests.get(urls[1])
            if r.status_code != 200:
                longurl = None
            else:
                longurl = r.url

            self.resolved_urls.append((urls[0], longurl))
            r.close()

        except requests.exceptions.RequestException:
            return None

    def fetch_url(self, url):
        # urlHandler = urllib2.urlopen(url[1])
        # print urlHandler
        # session = requests.Session()  # so connections are recycled
        resp = requests.head(url[1], allow_redirects=True, timeout=3)
        # if resp.status_code == 200 or resp.status_code == 302:
        self.resolved_urls.append((url[0], resp.url))
        resp.close()
        # print "appended"

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

    def aggregate_urls(self, tweets):
        urls_list = []
        resolved_urls = []
        bulk_count = 0
        bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
        # pool = ThreadPool(100)
        for tweet in tweets:
            # urls = re.findall(r'(https?://[^\s]+)', tweet["text"])
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                              tweet["text"])
            if len(urls) > 0:
                for url in urls:
                    urls_list.append((tweet["_id"], url))

        url_chunks = self.chunks(urls_list, 100)
        for chunk in url_chunks:

            pool = ThreadPool(100)
            pool.imap_unordered(self.fetch_url, chunk)
            pool.close()
            pool.join()
            pool.terminate()

            for tweet_id, long_url in self.resolved_urls:
                self.db_connection.add_to_bulk_upsert_push(query={"_id": tweet_id}, field=TWEET.RESOLVED_URLS,
                                                           value=long_url, bulk_op=bulk_op)

                bulk_count += 1

            try:
                if bulk_count != 0:
                    self.db_connection.end_bulk_upsert(bulk_op=bulk_op)
                    bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
                    logger.info("pushing %d updates to database" % bulk_count)
                    bulk_count = 0

            except InvalidOperation as e:
                logger.warn(e)

            urls_list = []
            # resolved_urls = []
            self.resolved_urls = []

        if bulk_count != 0:
            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)

    def get_tweet_urls(self, tweets):

        urls_list = []
        resolved_urls = []
        bulk_count = 0
        bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
        # pool = ThreadPool(100)
        for tweet in tweets:
            # urls = re.findall(r'(https?://[^\s]+)', tweet["text"])
            urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', tweet["text"])
            if len(urls) > 0:
                for url in urls:
                    urls_list.append((tweet["_id"], url))

        url_chunks = self.chunks(urls_list, 100)
        for chunk in url_chunks:



            # if len(urls_list) != 0 and len(urls_list) % 100 == 0:
                # threads = [threading.Thread(target=self.fetch_url, args=(url,)) for url in urls_list]
                # for thread in threads:
                #     thread.start()
                # for thread in threads:
                #     thread.join()
            pool = ThreadPool(100)
            pool.imap_unordered(self.fetch_url, chunk)
            pool.close()
            pool.join()
            pool.terminate()

                # rs = (grequests.head(u[1], timeout=2) for u in urls_list)
                # resolved = grequests.map(rs, exception_handler=exception_handler)
                # for index, long_url in enumerate(self.resolved_urls):
                # for tweet_id, long_url in self.resolved_urls:
                    # if long_url:
                        # long_url = long_url.url
                        # tweet_id = urls_list[index][0]

                    # for tweet_id, long_url in pool.map(self.resolve_url, urls_list):
                    #     resolved_urls.append((tweet_id, long_url))

            for tweet_id, long_url in self.resolved_urls:
                top10 = False
                top30 = False
                top50 = False
                doc = {
                    TWEET.VERIFIED_URLS: True
                }
                url = long_url.split("://")[1]
                if re.match(r'^www.', url):
                    try:
                        url = url.split("www.")[1]
                    except IndexError:
                        continue

                if "/" in url:
                    url = url.split("/")[0]

                if len(url.split('.')[0]) > 1:
                    # regexp = re.compile("/.*%s.*/" % url, re.IGNORECASE)
                    regexp = "/.*%s.*/" % url
                    # match = self.db_connection.find_document(collection=DB.TOP_NEWS_DOMAINS,
                    #                                          filter={"url": {"$regex": url}})

                    match = self.db_connection.find_document(collection=DB.TOP_NEWS_DOMAINS,
                                                             filter={"url": url})

                    for domain in match:
                        rank = domain["rank"]
                        if not top10:
                            top10 = rank <= 10

                        if not top30:
                            top30 = 11 <= rank <= 30

                        if not top50:
                            top50 = 31 <= rank <= 50



                    if top10:
                        doc[TWEET.CONTAINS_DOMAIN_TOP10] = top10

                    if top30:
                        doc[TWEET.CONTAINS_DOMAIN_TOP30] = top30

                    if top50:
                        doc[TWEET.CONTAINS_DOMAIN_TOP50] = top50

                self.db_connection.add_to_bulk_upsert(query={"_id": tweet_id}, data=doc, bulk_op=bulk_op)
                bulk_count += 1

            try:
                if bulk_count != 0:
                    self.db_connection.end_bulk_upsert(bulk_op=bulk_op)
                    bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
                    logger.info("pushing %d updates to database" % bulk_count)
                    bulk_count = 0

            except InvalidOperation as e:
                logger.warn(e)

            urls_list = []
            # resolved_urls = []
            self.resolved_urls = []

        if bulk_count != 0:
            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)

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
        bulk_count = 0
        for tweet in tweets:
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
            if TWEET.LINKS in tweet:
                for url in tweet[TWEET.LINKS]:
                    try:
                        url = requests.head(url, allow_redirects=True).url
                        url = url.split("://")[1]
                        if re.match(r'^www.', url):
                            try:
                                url = url.split("www.")[1]
                            except IndexError:
                                url = url.split("www3.")[1]

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
                    except ConnectionError as e:
                        logger.warn(e)

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
                TWEET.ENTITIES_COUNT: len(tweet[TWEET.ENTITIES]),
                TWEET.KEYWORDS_COUNT: len(tweet[TWEET.KEYWORDS]),
                TWEET.CONTAINS_DOMAIN_TOP10: top10,
                TWEET.CONTAINS_DOMAIN_TOP30: top30,
                TWEET.CONTAINS_DOMAIN_TOP50: top50
            }

            if len(tweet[TWEET.ENTITIES]) == 0:
                doc[TWEET.AVERAGE_ENTITY_CERTAINTY] = 0

            else:
                doc[TWEET.AVERAGE_ENTITY_CERTAINTY] = entity_certainty / len(tweet[TWEET.ENTITIES])

            if len(tweet[TWEET.KEYWORDS]) == 0:
                doc[TWEET.AVERAGE_KEYWORD_CERTAINTY] = 0
            else:
                doc[TWEET.AVERAGE_KEYWORD_CERTAINTY] = keyword_certainty / len(tweet[TWEET.KEYWORDS])
            # TWEET.AVERAGE_ENTITY_CERTAINTY: entity_certainty / len(tweet[TWEET.ENTITIES]),
            # TWEET.AVERAGE_KEYWORD_CERTAINTY: keyword_certainty / len(tweet[TWEET.KEYWORDS]),

            self.db_connection.add_to_bulk_upsert(query={"_id": tweet["_id"]},
                                                  data=doc, bulk_op=bulk_op)

            bulk_count += 1

            if bulk_count % 100 == 0:
                self.db_connection.end_bulk_upsert(bulk_op=bulk_op)
                bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)

        if bulk_count % 100 != 0:
            self.db_connection.end_bulk_upsert(bulk_op=bulk_op)

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
            if cursor_count > 0:
                for tweet in tweet_info:
                    total_favourites += tweet["favourites_count"]
                    total_retweets += tweet["retweet_count"]

                total_retweets = total_retweets / cursor_count
                total_favourites = total_favourites / cursor_count

            user_data = self.twitter.api.GetUser(user_id=user["_id"])
            created_at = datetime.strptime(user_data.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            final_date = datetime(year=2018, month=4, day=15)
            days_since = (final_date - created_at).days
            timestamp = calendar.timegm(created_at.timetuple())

            if user_data.status:
                doc = {
                    MP.IS_VERIFIED: user_data.verified,
                    MP.FRIENDS_COUNT: user_data.friends_count,
                    MP.AVERAGE_NO_FAVOURITES: total_favourites,
                    MP.AVERAGE_NO_RETWEETS: total_retweets,
                    MP.NON_EMPTY_DESCRIPTION: len(user_data.description) > 0,
                    MP.ACCOUNT_DAYS: days_since,
                    MP.CREATED_AT: created_at,
                    MP.CREATED_AT_EPOCH: timestamp
                }
            self.db_connection.find_and_update(collection=DB.MP_COLLECTION, query={"_id": user["_id"]},
                                               update={"$set": doc})

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

        for topic in topics:
            tweet_bulk_op = self.db_connection.start_bulk_upsert(collection=DB.RELEVANT_TWEET_COLLECTION)
            # matching_tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
            #                                                    filter={"$and":[{"text": {"$regex": " %s | #%s " % topic["name"],
            #                                                                     "$options": "-i"}},
            #                                                                    {"text": {
            #                                                                        "$regex": " #%s " % topic["name"],
            #                                                                        "$options": "-i"}}]})

            matching_tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                               filter={"text": {"$regex": " %s | #%s |%s | %s|#%s | #%s" %
                                                                                          (topic["name"], topic["name"],topic["name"],topic["name"],topic["name"],topic["name"]),
                                                                             "$options": "-i"}})

            # matching_tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
            #                                                    filter={"text": {"$regex": " %s | #" % topic["name"],
            #                                                                     "$options": "-i"}})


            # matching_tweets1 = list(matching_tweets1)
            #
            # matching_tweets2 = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
            #                                                    filter={"text": {"$regex": " #%s " % topic["name"],
            #                                                                     "$options": "-i"}})

            total = matching_tweets.count()
            print total
            tweet_length = 0
            contains_qm = 0
            contains_em = 0
            contains_multiple_marks = 0
            contains_happy_emoticon = 0
            contains_sad_emoticon = 0
            contains_happy_emoji = 0
            contains_sad_emoji = 0
            contains_pronouns = 0
            contains_uppercase = 0
            contains_figures = 0
            contains_url = 0
            contains_user_mention = 0
            contains_hashtag = 0
            contains_stock_symbols = 0
            sentiment_score = 0
            positive_sentiment = 0
            negative_sentiment = 0
            top10 = 0
            top30 = 0
            top50 = 0

            distinct_urls_count = 0
            most_visited_url_count = 0
            distinct_hashtag_count = 0
            most_used_hashtag_count = 0
            distinct_user_mention_count = 0
            most_mentioned_user_count = 0
            distinct_tweet_author_count = 0
            top_author_tweets_count = 0
            author_twitter_life = 0
            author_follower_count = 0
            author_friend_count = 0
            author_tweet_count = 0
            verified = 0
            day_relevance = 0
            week_relevance = 0
            two_week_relevance = 0
            words_not_in_dict = 0

            # Distinctions

            distinct_urls = {}
            distinct_hashtags = {}
            distinct_user_mentions = {}
            distinct_authors = {}

            # total_tweets = list(matching_tweets1) + list(matching_tweets2)

            if total > 0:
                for tweet in matching_tweets:
                    self.db_connection.add_to_bulk_upsert_addtoset(query={TWEET.ID: tweet["_id"]},
                                                                   field=TWEET.TOPICS,
                                                                   value={"_id": topic["_id"], TOPIC.IDENTIFIED_AS_TOPIC: topic[TOPIC.IDENTIFIED_AS_TOPIC]},
                                                                   bulk_op=tweet_bulk_op)

                                                                             # {"_id": topic["_id"],
                                                        # TOPIC.IDENTIFIED_AS_TOPIC: topic[TOPIC.IDENTIFIED_AS_TOPIC]}}},
                                                        #   bulk_op=tweet_bulk_op)

                    tweet_length += tweet[TWEET.CHARACTER_COUNT]
                    if tweet[TWEET.CONTAINS_QM]:
                        contains_qm += 1

                    if tweet[TWEET.CONTAINS_EM]:
                        contains_em += 1

                    if tweet[TWEET.CONTAINS_MULTIPLE_MARKS]:
                        contains_multiple_marks += 1

                    if tweet[TWEET.CONTAINS_HAPPY_EMOTICON]:
                        contains_happy_emoticon += 1

                    if tweet[TWEET.CONTAINS_SAD_EMOTICON]:
                        contains_sad_emoticon += 1

                    if tweet[TWEET.CONTAINS_HAPPY_EMOJI]:
                        contains_happy_emoji += 1

                    if tweet[TWEET.CONTAINS_SAD_EMOJI]:
                        contains_sad_emoji += 1

                    if tweet[TWEET.CONTAINS_PRONOUNS]:
                        contains_pronouns += 1

                    if tweet[TWEET.CONTAINS_FIGURES]:
                        contains_figures += 1

                    if tweet[TWEET.FRACTION_CAPITALISED] >= 0.3:
                        contains_uppercase += 1

                    urls = re.findall(r'(https?://[^\s]+)', tweet[TWEET.TEXT])
                    if len(urls) > 0:
                        contains_url += 1
                        if TWEET.RESOLVED_URLS in tweet:
                            for c, url in enumerate(tweet[TWEET.RESOLVED_URLS]):
                                if url not in distinct_urls:
                                    if url.split("//")[1].split("/")[0] != "twitter.com":  # Ignore twitter domain URLs
                                        distinct_urls[url] = 1

                                else:
                                    distinct_urls[url] = distinct_urls[url] + 1


                    if tweet[TWEET.MENTIONS_USER]:
                        contains_user_mention += 1

                    if TWEET.MENTIONED_USERS in tweet:
                        if len(tweet[TWEET.MENTIONED_USERS]) > 0:
                            for mentioned_user in tweet[TWEET.MENTIONED_USERS]:
                                if mentioned_user not in distinct_user_mentions:
                                    distinct_user_mentions[mentioned_user] = 1

                                else:
                                    distinct_user_mentions[mentioned_user] = distinct_user_mentions[mentioned_user] + 1

                    if TWEET.HASHTAGS in tweet:
                        if len(tweet[TWEET.HASHTAGS]) > 0:
                            contains_hashtag += 1
                            for hashtag in tweet[TWEET.HASHTAGS]:
                                if hashtag not in distinct_hashtags:
                                    distinct_hashtags[hashtag] = 1

                                else:
                                    distinct_hashtags[hashtag] = distinct_hashtags[hashtag] + 1

                    if tweet[TWEET.CONTAINS_STOCK_SYMBOL]:
                        contains_stock_symbols += 1

                    sentiment_score += tweet[TWEET.SENTIMENT_SCORE]
                    if tweet[TWEET.SENTIMENT_SCORE] >= 0:
                        positive_sentiment += 1

                    if tweet[TWEET.SENTIMENT_SCORE] < 0:
                        negative_sentiment += 1

                    if tweet[TWEET.CONTAINS_DOMAIN_TOP10]:
                        top10 += 1

                    if tweet[TWEET.CONTAINS_DOMAIN_TOP30]:
                        top30 += 1

                    if tweet[TWEET.CONTAINS_DOMAIN_TOP50]:
                        top50 += 1

                    author_info = self.db_connection.find_document(collection=DB.MP_COLLECTION,
                                                                   filter={"_id": tweet[TWEET.AUTHOR_ID]})[0]

                    if author_info[MP.TWITTER_HANDLE] not in distinct_authors:
                        distinct_authors[author_info[MP.TWITTER_HANDLE]] = 1
                        if author_info[MP.IS_VERIFIED]:
                            verified += 1

                        author_twitter_life += author_info[MP.ACCOUNT_DAYS]
                        author_follower_count += author_info[MP.FOLLOWERS_COUNT]
                        author_friend_count += author_info[MP.FRIENDS_COUNT]
                        author_tweet_count += author_info[MP.TWEET_COUNT]

                    else:
                        distinct_authors[author_info[MP.TWITTER_HANDLE]] = distinct_authors[
                                                                               author_info[MP.TWITTER_HANDLE]] + 1

                        # if author_info[MP.IS_VERIFIED]:
                        #     verified += 1

                    day_relevance += tweet[TWEET.RELEVANCY_DAY]
                    week_relevance += tweet[TWEET.RELEVANCY_WEEK]
                    two_week_relevance += tweet[TWEET.RELEVANCY_TWO_WEEKS]
                    words_not_in_dict += tweet[TWEET.FRAC_NOT_IN_DICT]

                distinct_urls_count += len(distinct_urls)
                if distinct_urls_count > 0:
                    top_url = max(distinct_urls.iteritems(), key=operator.itemgetter(1))[0]

                distinct_hashtag_count += len(distinct_hashtags)
                if distinct_hashtag_count > 0:
                    top_hashtag = max(distinct_hashtags.iteritems(), key=operator.itemgetter(1))[0]

                distinct_user_mention_count += len(distinct_user_mentions)
                if distinct_user_mention_count > 0:
                    top_user_mention = max(distinct_user_mentions.iteritems(), key=operator.itemgetter(1))[0]

                distinct_tweet_author_count += len(distinct_authors)
                if distinct_tweet_author_count > 0:
                    top_author = max(distinct_authors.iteritems(), key=operator.itemgetter(1))[0]

                # for tweet in matching_tweets:
                #     if top_url in tweet[TWEET.RESOLVED_URLS]:
                #         most_visited_url_count += 1
                #
                #     if top_hashtag in tweet[TWEET.HASHTAGS]:
                #         most_used_hashtag_count += 1
                #
                #     if top_user_mention in tweet[TWEET.MENTIONED_USERS]:
                #         most_mentioned_user_count += 1
                #
                #     if tweet[TWEET.AUTHOR_HANDLE] == top_author:
                #         top_author_tweets_count += 1

                doc = {
                        TOPIC.TWEET_COUNT: total,
                        TOPIC.TWEET_AVERAGE_LENGTH: tweet_length / total,
                        TOPIC.FRAC_CONTAINING_QM: contains_qm / total,
                        TOPIC.FRAC_CONTAINING_EM: contains_em / total,
                        TOPIC.FRAC_CONTAINING_MULTIPLE_MARKS: contains_multiple_marks / total,
                        TOPIC.FRAC_CONTAINING_HAPPY_EMOTICON: contains_happy_emoticon / total,
                        TOPIC.FRAC_CONTAINING_SAD_EMOTICON: contains_sad_emoticon / total,
                        TOPIC.FRAC_CONTAINING_HAPPY_EMOJI: contains_happy_emoji / total,
                        TOPIC.FRAC_CONTAINING_SAD_EMOJI: contains_sad_emoji / total,
                        TOPIC.FRAC_CONTAINING_PRONOUNS: contains_pronouns / total,
                        TOPIC.FRAC_CONTAINING_FIGURES: contains_figures / total,
                        TOPIC.FRAC_CONTAINING_UPPERCASE: contains_uppercase / total,
                        TOPIC.FRAC_CONTAINING_URL: contains_url / total,
                        TOPIC.FRAC_CONTAINING_USER_MENTION: contains_user_mention / total,
                        TOPIC.FRAC_CONTAINING_HASHTAGS: contains_hashtag / total,
                        TOPIC.FRAC_CONTAINING_STOCK_SYMBOLS: contains_stock_symbols / total,
                        TOPIC.AVERAGE_SENTIMENT_SCORE: sentiment_score / total,
                        TOPIC.FRAC_CONTAINING_POSITIVE_SENTIMENT: positive_sentiment / total,
                        TOPIC.FRAC_CONTAINING_NEGATIVE_SENTIMENT: negative_sentiment / total,
                        TOPIC.FRAC_CONTAINING_DOMAIN10: top10 / total,
                        TOPIC.FRAC_CONTAINING_DOMAIN30: top30 / total,
                        TOPIC.FRAC_CONTAINING_DOMAIN50: top50 / total,
                        TOPIC.DISTINCT_URLS_COUNT: distinct_urls_count,
                        TOPIC.DISTINCT_HASHTAG_COUNT: distinct_hashtag_count,
                        TOPIC.DISTINCT_USER_MENTION_COUNT: distinct_user_mention_count,
                        TOPIC.DISTINCT_TWEET_AUTHOR_COUNT: distinct_tweet_author_count,
                        TOPIC.AVERAGE_AUTHOR_TWITTER_LIFE: author_twitter_life / distinct_tweet_author_count,
                        TOPIC.AVERAGE_AUTHOR_TWEET_COUNT: author_tweet_count / distinct_tweet_author_count,
                        TOPIC.AVERAGE_AUTHOR_FOLLOWER_COUNT: author_follower_count / distinct_tweet_author_count,
                        TOPIC.AVERAGE_AUTHOR_FRIEND_COUNT: author_friend_count / distinct_tweet_author_count,
                        TOPIC.FRAC_FROM_VERIFIED: verified / distinct_tweet_author_count,
                        TOPIC.AVERAGE_DAY_RELEVANCE: day_relevance / total,
                        TOPIC.AVERAGE_WEEK_RELEVANCE: week_relevance / total,
                        TOPIC.AVERAGE_2WEEK_RELEVANCE: two_week_relevance / total,
                        TOPIC.AVERAGE_WORDS_NOT_IN_DICT: words_not_in_dict / total,
                    }

                if distinct_urls_count > 0:
                    doc[TOPIC.FRAC_CONTAINING_MOST_VISITED_URL] = distinct_urls.get(top_url) / total

                else:
                    doc[TOPIC.FRAC_CONTAINING_MOST_VISITED_URL] = 0

                if distinct_hashtag_count > 0:
                    doc[TOPIC.FRAC_CONTAINING_MOST_USED_HASHTAG] = distinct_hashtags.get(top_hashtag) / total

                else:
                    doc[TOPIC.FRAC_CONTAINING_MOST_USED_HASHTAG] = 0

                if distinct_user_mention_count > 0:
                    doc[TOPIC.FRAC_CONTAINING_MOST_MENTIONED_USER] = distinct_user_mentions.get(top_user_mention) / total

                else:
                    doc[TOPIC.FRAC_CONTAINING_MOST_MENTIONED_USER] = 0

                if distinct_tweet_author_count > 0:
                    doc[TOPIC.FRAC_CONTAINING_TOP_AUTHOR] = distinct_authors.get(top_author) / total

                else:
                    doc[TOPIC.FRAC_CONTAINING_TOP_AUTHOR] = 0


                # self.db_connection.update_many(collection=DB.RELEVANT_TWEET_COLLECTION,
                #                                query={"$in": tweet_id_list},
                #                                update={"$push": {TWEET.TOPICS: {"_id": topic["_id"],
                #                                         TOPIC.IDENTIFIED_AS_TOPIC: topic[TOPIC.IDENTIFIED_AS_TOPIC]}}})
                self.db_connection.find_and_update(
                    collection=DB.RELEVANT_TOPICS,
                    query={"_id": topic["_id"]},
                    update={"$set": doc})

                self.db_connection.end_bulk_upsert(bulk_op=tweet_bulk_op)

    def get_topics_for_lost_tweets(self):
        tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                  filter={"$and": [{"aggregate_label":{"$exists":True}},
                                                                   {"topics":{"$exists":False}}]})

        for tweet in tweets:
            print tweet['text']
            topic = raw_input("topic:\n")
            possible_topic = self.db_connection.find_document(collection=DB.RELEVANT_TOPICS,
                                                              filter={"name": topic.lower()})

            if possible_topic.count() > 0:
                found_topic = possible_topic.next()
                self.db_connection.find_and_update(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                   query={"_id": tweet["_id"]},
                                                   update={"$set": {"topics": [{"_id": found_topic["_id"],
                                                                                TOPIC.IDENTIFIED_AS_TOPIC: found_topic[TOPIC.IDENTIFIED_AS_TOPIC]}]}})


if __name__ == "__main__":
    ft = FeatureExtractor()
    # ft.get_top_websites()
    # tweets = ft.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
    #                                         filter={TWEET.VERIFIED_URLS: {"$exists": False}})

    # tweets = ft.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
    #                                         filter={TWEET.RESOLVED_URLS: {"$exists": False}}, projection={"text": 1})
    # tweets = ft.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
    #                                         filter={TWEET.TEXT: {"$regex": ".com"}})
                                            # filter={TWEET.VERIFIED_URLS: {"$exists": False}})

    # print tweets.count()
    # ft.get_extra_features(tweets)
    # ft.aggregate_urls(tweets)
    # ft.get_tweet_urls(tweets)
    # users = ft.db_connection.find_document(collection=DB.MP_COLLECTION, filter={})
    # ft.get_user_features(users=users)
    # ft.get_tweet_features(tweets=tweets)
    # topics = ft.db_connection.find_document(collection=DB.RELEVANT_TOPICS,
    #                                         filter={TOPIC.TWEET_COUNT: {"$exists": False}})
    topics = ft.db_connection.find_document(collection=DB.RELEVANT_TOPICS)
    ft.get_topic_features(topics=topics)
    # ft.get_topics_for_lost_tweets()