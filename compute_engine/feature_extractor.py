# coding=utf-8
from __future__ import unicode_literals
from __future__ import division
import calendar
import os
import re
from collections import Counter

import nltk
import emoji
import logging
from datetime import datetime

import operator
import requests
from bs4 import BeautifulSoup

from requests.exceptions import ConnectionError
from db_engine import DBConnection
from ingest_engine.twitter_ingest import Twitter
from cons import DB, EMOJI_HAPPY, EMOJI_UNHAPPY, CREDS, MP, DOMAIN, TWEET, WEEKDAY, TOPIC
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
            matching_tweets = self.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                                               filter={"text": {"$regex": topic["name"],
                                                                                "$options": "-i"}})

            total = matching_tweets.count()
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
            verified = 0
            day_relevance = 0
            week_relevance = 0
            two_week_relevance = 0

            # Distinctions

            distinct_urls = {}
            distinct_hashtags = {}
            distinct_user_mentions = {}
            distinct_authors = {}

            if total > 0:
                for tweet in matching_tweets:
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

                    if tweet[TWEET.FRACTION_CAPITALISED] >= 0.3:
                        contains_uppercase += 1

                    if len(tweet[TWEET.LINKS]) > 1:
                        contains_url += 1
                        for c, url in enumerate(tweet[TWEET.LINKS]):
                            if c != 0: # Only adds URLs that are not the URL of the actual tweet
                                if url not in distinct_urls:
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


                    contains_multiple_marks += tweet[TWEET.CONTAINS_MULTIPLE_MARKS]
                    contains_happy_emoticon += tweet_length[TWEET]

                    author_info = self.db_connection.find_document(collection=DB.MP_COLLECTION,
                                                                   filter={"_id": tweet[TWEET.AUTHOR_ID]})

                    author_twitter_life += author_info[MP.ACCOUNT_DAYS]
                    author_follower_count += author_info[MP.FOLLOWERS_COUNT]
                    author_friend_count += author_info[MP.FRIENDS_COUNT]

                    if author_info[MP.TWITTER_HANDLE] not in distinct_authors:
                        distinct_authors[author_info[MP.TWITTER_HANDLE]] = 1
                        if author_info[MP.IS_VERIFIED]:
                            verified += 1
                    else:
                        distinct_authors[author_info[MP.TWITTER_HANDLE]] = distinct_authors[
                                                                               author_info[MP.TWITTER_HANDLE]] + 1

                        if author_info[MP.IS_VERIFIED]:
                            verified += 1

                    day_relevance += tweet[TWEET.RELEVANCY_DAY]
                    week_relevance += tweet[TWEET.RELEVANCY_WEEK]
                    two_week_relevance += tweet[TWEET.RELEVANCY_TWO_WEEKS]

                distinct_urls_count += len(distinct_urls)
                top_url = max(distinct_urls.iteritems(), key=operator.itemgetter(1))[0]
                distinct_hashtag_count += len(distinct_hashtags)
                top_hashtag = max(distinct_hashtags.iteritems(), key=operator.itemgetter(1))[0]
                distinct_user_mention_count += len(distinct_user_mentions)
                top_user_mention = max(distinct_user_mentions.iteritems(), key=operator.itemgetter(1))[0]
                distinct_tweet_author_count += len(distinct_authors)
                top_author = max(distinct_authors.iteritems(), key=operator.itemgetter(1))[0]

                for tweet in matching_tweets:
                    if top_url in tweet[TWEET.LINKS]:
                        most_visited_url_count += 1

                    if top_hashtag in tweet[TWEET.HASHTAGS]:
                        most_used_hashtag_count += 1

                    if top_user_mention in tweet[TWEET.MENTIONED_USERS]:
                        most_mentioned_user_count += 1

                    if tweet[TWEET.AUTHOR_HANDLE] == top_author:
                        top_author_tweets_count += 1

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
                        TOPIC.FRAC_CONTAINING_MOST_VISITED_URL: most_visited_url_count / total,
                        TOPIC.DISTINCT_HASHTAG_COUNT: distinct_hashtag_count,
                        TOPIC.FRAC_CONTAINING_MOST_USED_HASHTAG: most_used_hashtag_count / total,
                        TOPIC.DISTINCT_USER_MENTION_COUNT: distinct_user_mention_count,
                        TOPIC.FRAC_CONTAINING_MOST_MENTIONED_USER: most_mentioned_user_count / total,
                        TOPIC.DISTINCT_TWEET_AUTHOR_COUNT: distinct_tweet_author_count,
                        TOPIC.FRAC_CONTAINING_TOP_AUTHOR: top_author_tweets_count / total,
                        TOPIC.AVERAGE_AUTHOR_TWITTER_LIFE: author_twitter_life / distinct_tweet_author_count,
                        TOPIC.AVERAGE_AUTHOR_TWEET_COUNT: total / distinct_tweet_author_count,
                        TOPIC.AVERAGE_AUTHOR_FOLLOWER_COUNT: author_follower_count / distinct_tweet_author_count,
                        TOPIC.AVERAGE_AUTHOR_FRIEND_COUNT: author_friend_count / distinct_tweet_author_count,
                        TOPIC.FRAC_FROM_VERIFIED: verified / distinct_tweet_author_count,
                        TOPIC.AVERAGE_DAY_RELEVANCE: day_relevance / total,
                        TOPIC.AVERAGE_WEEK_RELEVANCE: week_relevance / total,
                        TOPIC.AVERAGE_2WEEK_RELEVANCE: two_week_relevance / total
                    }

                self.db_connection.find_and_update(
                    collection=DB.RELEVANT_TOPICS,
                    query={"_id": topic["_id"]},
                    update={"$set": doc})







if __name__ == "__main__":
    ft = FeatureExtractor()
    # ft.get_top_websites()
    tweets = ft.db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                            filter={"word_count": {"$exists": False}})
    # users = ft.db_connection.find_document(collection=DB.MP_COLLECTION, filter={})
    # ft.get_user_features(users=users)
    ft.get_tweet_features(tweets=tweets)
    # topics = ft.db_connection.find_document(collection=DB.RELEVANT_TOPICS)
    # ft.get_topic_features(topics=topics)