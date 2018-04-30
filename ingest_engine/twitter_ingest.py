import calendar
import sys

import re
from operator import itemgetter

import requests
from urllib3.exceptions import NewConnectionError

sys.path.append("..")
from python_twitter_fork import twitter
from python_twitter_fork.twitter.error import TwitterError
from db_engine import DBConnection
from cons import DB, CREDS, MP, TWEET, WOEIDS, TWITTER_TREND
import os
import time
from datetime import datetime
import logging
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
logger = logging.getLogger(__name__)


class Twitter(object):
    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret, db_connection):
        self.logger = logging.getLogger(__name__)
        self.db_connection = db_connection
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token_key = access_token_key
        self.access_token_secret = access_token_secret
        self.session = requests.session()
        self.api = twitter.Api(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token_key=self.access_token_key,
            access_token_secret=self.access_token_secret,
            sleep_on_rate_limit=True
        )

    def process_embeds(self):
        tweet_list = self.db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                                   filter={"html": {"$exists": False}},
                                                   projection={"twitter_handle": 1, "retweet_count": 1})
        for tweet in tweet_list:
            self.get_embed(status_id=tweet["_id"])

        tweet_list.close()

    def print_embed(self, status_id):
        tweet_list = self.db_connection.find_document(collection=DB.TWEET_COLLECTION,
                                                      filter={"html": {"$exists": True}},
                                                      projection={"twitter_handle": 1, "retweet_count": 1, "html":1})

        print tweet_list[0]['html']

    def get_embed(self, status_id):
        html = self.api.GetStatusOembed(status_id=status_id)['html']
        self.db_connection.update_tweet(tweet_id=status_id, update={"html": html})
        return html

    def get_status(self, tweet_id):
        return self.api.GetStatus(status_id=tweet_id)

    def get_historic_trends(self, month, day):
        trends_to_insert = []
        link = "https://trendogate.com/placebydate/23424975/2018-%s-%s" % (month, day)
        response = self.session.get(link)
        if response.status_code == 200:
            page = response.content
        else:
            raise requests.ConnectionError("Couldn't connect to that URL.")

        soup = BeautifulSoup(page, 'html.parser')
        # for ultag in soup.find_all('ul', {'class': 'my_class'}):
        for entry in soup.findAll('ul', {'class': 'list-group'}):
            for litag in entry.find_all('li'):
                date = datetime(year=2018, month=month, day=day, hour=12)
                trend_doc = {
                    TWITTER_TREND.NAME: litag.text,
                    TWITTER_TREND.TIMESTAMP: date,
                    TWITTER_TREND.TIMESTAMP_EPOCH: calendar.timegm(date.timetuple()),
                    TWITTER_TREND.LOCATION: "United Kingdom",
                }
                trends_to_insert.append(trend_doc)

        self.db_connection.bulk_insert(data=trends_to_insert, collection=DB.TWITTER_TRENDS)
        logger.info("Inserted twitter trends for: %s/%s/2018" % (day, month))

    def get_trends(self, location=WOEIDS.UK, globally=False):
        """
        Collect trends based on Location given by woeid: http://woeid.rosselliot.co.nz/lookup
        :param location: woeid
        :param globally: Boolean indicating whether to get global trends
        :return:
        """
        trends_to_insert = []

        if globally:
            trends = self.api.GetTrendsCurrent()

        else:
            trends = self.api.GetTrendsWoeid(woeid=location)

        for trend in trends:
            trend = trend._json

            trend_doc = {
                TWITTER_TREND.NAME: trend[TWITTER_TREND.NAME],
                TWITTER_TREND.URL: trend[TWITTER_TREND.URL],
                TWITTER_TREND.TIMESTAMP: datetime.now(),
                TWITTER_TREND.TIMESTAMP_EPOCH: time.time()
            }

            if globally:
                trend_doc[TWITTER_TREND.LOCATION] = "Global"

            else:
                if location == WOEIDS.UK:
                    trend_doc[TWITTER_TREND.LOCATION] = "United Kingdom"

                elif location == WOEIDS.USA:
                    trend_doc[TWITTER_TREND.LOCATION] = "United States"

            if trend[TWITTER_TREND.TWEET_VOLUME]:  # If there is a value for tweet volume on this trend
                trend_doc[TWITTER_TREND.TWEET_VOLUME] = trend[TWITTER_TREND.TWEET_VOLUME]

            trends_to_insert.append(trend_doc)

        self.db_connection.bulk_insert(data=trends_to_insert, collection=DB.TWITTER_TRENDS)

    def get_tweets(self, mp_doc, historic=False):
        '''
        Collect tweets for a given MP, updates number of tweets collected for an MP
        If number of collected tweets is less than the amount of tweets this MP has it'll carry on
        :param mp_doc: mongo document for mp we are collecting tweets for, projection is applied
        :param historic: Old tweets being fetched or not
        :return:
        '''

        tweet_list = []
        retweet_list = []
        user_id = mp_doc[MP.ID]
        twitter_handle = mp_doc[MP.TWITTER_HANDLE]
        tweet_count = mp_doc[MP.TWEET_COUNT]
        tweets_collected = mp_doc[MP.TWEETS_COLLECTED]
        tracked_ids = []
        if MP.OLDEST_ID in mp_doc:
            oldest_id = mp_doc[MP.OLDEST_ID]

        if MP.NEWEST_ID in mp_doc:
            newest_id = mp_doc[MP.NEWEST_ID]

        raw_tweets = self.api.GetUserTimeline(user_id=user_id,
                                              count=200,
                                              exclude_replies=False,
                                              include_rts=True,
                                              since_id=newest_id,
                                              )
        # Only collect tweets while the amount collected is less than the available for that MP
        while tweets_collected < tweet_count or len(raw_tweets) > 1 or not newest_id:
            if historic:
                raw_tweets = self.api.GetUserTimeline(user_id=user_id,
                                                      count=200,
                                                      exclude_replies=False,
                                                      include_rts=True,
                                                      max_id=oldest_id,
                                                      )
            else:
                raw_tweets = self.api.GetUserTimeline(user_id=user_id,
                                                      count=200,
                                                      exclude_replies=False,
                                                      include_rts=True,
                                                      since_id=newest_id,
                                                      )


            # Sort tweets by oldest first
            raw_tweets = sorted(raw_tweets, key=lambda tweet: (tweet.created_at_in_seconds))
            # raw_tweets = raw_tweets[::-1]

            if not raw_tweets or len(raw_tweets) == 1 or len(raw_tweets) == 2 or raw_tweets[0].id in tracked_ids:  # Break if API limit reached

                break

            tweets_collected += len(raw_tweets)
            for raw_tweet in raw_tweets:
                tracked_ids.append(raw_tweet.id)
                retweet = False

                # Tweet count
                tweet_count = raw_tweet.user.statuses_count

                if raw_tweet.retweeted_status:
                    retweet_user = raw_tweet.full_text.split(" ")[1].split(":")[0]
                    retweet = True
                    raw_tweet = raw_tweet.retweeted_status

                if historic:
                    if raw_tweet.id < oldest_id or not oldest_id:
                        oldest_id = raw_tweet.id

                else:
                    if raw_tweet.id > newest_id or not newest_id:
                        newest_id = raw_tweet.id

                formatted_tweet = {
                    TWEET.ID: raw_tweet.id,
                    TWEET.TEXT: raw_tweet.full_text,
                    TWEET.AUTHOR_ID: user_id,
                    TWEET.AUTHOR_HANDLE: twitter_handle,
                    TWEET.FAVOURITES_COUNT: raw_tweet.favorite_count,
                    TWEET.RETWEET_COUNT: raw_tweet.retweet_count,
                    TWEET.LAST_UPDATED: datetime.now()
                }

                # Tweet dates
                date = datetime.strptime(raw_tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')
                timestamp = calendar.timegm(date.timetuple())
                formatted_tweet[TWEET.CREATED_AT] = date
                formatted_tweet[TWEET.CREATED_AT_EPOCH] = timestamp

                # Tweet hashtags
                hashtags = []
                for hashtag in raw_tweet.hashtags:
                    hashtags.append(hashtag.text)

                if hashtags:
                    formatted_tweet[TWEET.HASHTAGS] = hashtags

                # Tweet URLs
                url = None
                if raw_tweet.urls:
                    url = raw_tweet.urls[0].url
                    formatted_tweet[TWEET.URL] = url

                # Links in URL
                link_list = []
                potential_links = re.findall(r'(https?://[^\s]+)', raw_tweet.full_text)
                for link in potential_links:  # Only add links that are not the tweet URL
                    if not url or link != url:
                        link_list.append(link)

                if link_list:
                    formatted_tweet[TWEET.LINKS] = link_list

                # Retweet handling
                if retweet:
                    formatted_tweet[TWEET.AUTHOR_HANDLE] = retweet_user
                    formatted_tweet[TWEET.RETWEETER_HANDLE] = twitter_handle
                    retweet_list.append(formatted_tweet)

                else:
                    tweet_list.append(formatted_tweet)

            if tweet_list:
                self.db_connection.insert_tweets(tweet_list)
                tweet_list = []

            if retweet_list:
                self.db_connection.insert_tweets(tweet_list=retweet_list, retweets=True)
                retweet_list = []

        if historic:
            self.db_connection.update_mp(user_id=user_id, update={MP.OLDEST_ID: oldest_id,
                                                                  MP.TWEET_COUNT: tweet_count,
                                                                  MP.TWEETS_COLLECTED: tweets_collected})

        else:
            self.db_connection.update_mp(user_id=user_id, update={MP.NEWEST_ID: newest_id,
                                                                  MP.TWEET_COUNT: tweet_count,
                                                                  MP.TWEETS_COLLECTED: tweets_collected})

    def verify_credentials(self):
        return self.api.VerifyCredentials()

    def get_timeline(self, user):
        tweets = self.api.GetUserTimeline(screen_name=user,
                                          count=200,
                                          exclude_replies=False,
                                          include_rts=False)

    def get_user_data(self, user_id):
        try:
            data = self.api.GetUser(user_id=user_id)
        except:
            self.logger.warning("Twitter ID not found: %s" % user_id)

        if data.status:  # This MP has tweeted
            user_dict = {
                'description': data.description,
                'followers_count': data.followers_count,
                'tweet_count': data.statuses_count,
                'newest_id': data.status.id,
                'oldest_id': data.status.id
            }

            self.db_connection.update_mp(data.id, user_dict)

        else:
            self.logger.warning("MP: %s - has not tweeted" % user_id)

    def new_mp(self, twitter_handle):
        try:
            data = self.api.GetUser(screen_name=twitter_handle)
        except:
            self.logger.warning("Twitter handle not found: %s" % twitter_handle)
            return {}

        user_dict = {
            'description': data.description,
            'followers_count': data.followers_count,
            'tweet_count': data.statuses_count,
            'newest_id': data.status.id,
            '_id': data.id,
            'twitter_handle': "@%s" % data.screen_name
        }
        self.db_connection.create_mp(user_dict)

    def get_update_tweets(self, mp_doc, historic=False):
        '''
        :param historic: States whether old tweets are being fetched or not
        :param mp_doc: Document for mp returned from find projection
        :return: A list of dicts representing a tweet each pushed to DB
        '''

        calls_to_api = 0
        user_id = mp_doc["_id"]
        oldest_id = None
        newest_id = None
        if "oldest_id" in mp_doc:
            oldest_id = mp_doc["oldest_id"]

        if "newest_id" in mp_doc:
            newest_id = mp_doc["newest_id"]

        twitter_handle = mp_doc["twitter_handle"]
        tweets_available = True
        old_tweets = []



        while tweets_available:
            try:
                # if oldest_id or newest_id:
                if historic:
                    tweets = self.api.GetUserTimeline(user_id=user_id,
                                                      count=200,
                                                      exclude_replies=False,
                                                      include_rts=True,
                                                      max_id=oldest_id,
                                                      trim_user=True,
                                                      )
                else:
                    tweets = self.api.GetUserTimeline(user_id=user_id,
                                                      count=200,
                                                      exclude_replies=False,
                                                      include_rts=True,
                                                      since_id=newest_id,
                                                      trim_user=True
                                                      )
                # else:
                #     break
            except (TwitterError, ConnectionError):
                self.logger.info("Rate limit for twitter reached.. now sleeping")
                time.sleep(60 * 16)
                self.get_update_tweets(mp_doc=mp_doc, historic=historic)
                break

            if tweets:
                calls_to_api += 1
                if old_tweets != tweets:
                    tweet_list = []
                    retweet_list = []
                    similar_count = 0  # Track how many of the same tweets have appeared
                    for tweet in tweets:
                        retweet = False
                        if historic:
                            if tweet.retweeted_status:
                                retweet_user = tweet.full_text.split(" ")[1].split(":")[0]
                                retweet = True
                                tweet = tweet.retweeted_status

                            if tweet.id < oldest_id or not oldest_id:
                                oldest_id = tweet.id

                            elif tweet.id == oldest_id:
                                similar_count += 1
                                if similar_count == 2:
                                    tweets_available = False
                                    break

                            else:
                                break

                        else:
                            if tweet.id > newest_id or not newest_id:
                                newest_id = tweet.id

                            elif tweet.id == newest_id:
                                similar_count += 1
                                if similar_count == 2:
                                    tweets_available = False
                                    break

                            else:
                                tweets_available = False
                                break

                        formatted_tweet = {
                            "_id": tweet.id,
                            "text": tweet.full_text,
                            "author_id": user_id,
                            "author_handle": twitter_handle,
                            "favourite_count": tweet.favorite_count,
                            "retweet_count": tweet.retweet_count,
                            "last_updated": datetime.now()
                        }

                        # Sun May 21 17:36:44 +0000 2017
                        date = datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')
                        formatted_tweet["created_at"] = date

                        hashtags = []
                        for hashtag in tweet.hashtags:
                            hashtags.append(hashtag.text)

                        if hashtags:
                            formatted_tweet["hashtags"] = hashtags

                        if tweet.urls:
                            url = tweet.urls[0].url
                            formatted_tweet["url"] = url

                        if retweet:
                            formatted_tweet["author_handle"] = retweet_user
                            formatted_tweet["retweeter_handle"] = twitter_handle
                            retweet_list.append(formatted_tweet)

                        else:
                        # self.db_connection.insert_tweet(formatted_tweet)
                            tweet_list.append(formatted_tweet)

                    old_tweets = tweets
                    self.db_connection.insert_tweets(tweet_list)  # Insert in batches of 200
                    if retweet_list:
                        self.db_connection.insert_tweets(tweet_list=retweet_list, retweets=True)
                else:
                    tweets_available = False

            else:  # Have reached the oldest tweets
                tweets_available = False

        if historic:
            self.db_connection.update_mp(user_id=user_id, update={"oldest_id": oldest_id})

        else:
            self.db_connection.update_mp(user_id=user_id, update={"newest_id": newest_id})

        return calls_to_api

    def update_all_mps(self):
        for mp in self.db_connection.find_document(collection=DB.MP_COLLECTION,
                                                   filter={"newest_id": {"$exists": True}},
                                                   projection={"oldest_id": 1}):

            self.get_user_data(mp["_id"])

    def update_all_tweets(self, historic=False):
        mp_list = self.db_connection.find_document(collection=DB.MP_COLLECTION,
                                              filter={},
                                              projection={"twitter_handle": 1, "oldest_id": 1,
                                                          "newest_id": 1, "tweet_count": 1, "tweets_collected": 1})
        for mp in mp_list:
            if "twitter_handle" in mp:
                self.logger.info("Updating ALL tweets for: %s" % mp["twitter_handle"])
                self.get_tweets(mp_doc=mp, historic=historic)

        mp_list.close()
        logger.info("Tweet ingest complete")

def main():
    db_connection = DBConnection()
    twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
                          os.environ.get(CREDS.TWITTER_SECRET),
                          os.environ.get(CREDS.TWITTER_TOKEN),
                          os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
                          db_connection)

    if "trends" in sys.argv:
        if "historic" in sys.argv:
            date = datetime.today()
            day_end = date.day - 1
            month_end = date.month
            month = 1
            day = 2
            while month != month_end or day != day_end:
                twitter_api.get_historic_trends(month=month, day=day)
                time.sleep(3)
                day += 1
                if day % 30 == 0:
                    month += 1
                    day = 1

        globally = "global" in sys.argv
        is_uk = "UK" in sys.argv

        location = WOEIDS.UK
        if not is_uk and len(sys.argv) > 2:  # Check that no location has be inputted
            location = WOEIDS.USA

        while True:
            twitter_api.get_trends(location=location, globally=globally)
            time.sleep(60*60*2)  # Run every 2 hours

    elif "tweets" in sys.argv:
        historic = "historical" in sys.argv
        while True:
            twitter_api.update_all_tweets(historic=historic)
            if historic:
                break



if __name__ == "__main__":
    try:
        main()

    except NewConnectionError as e:
        logger.info("Restarting script due to %s" % e.message)
        main()

    except ConnectionError as e:
        logger.info("Restarting script due to %s" % e.message)
        main()

    except TwitterError as e:
        logger.info("Twitter API errors: %s ----- sleeping for 15 mins" % e.message)
        time.sleep(60 * 15)
        main()

    # db_connection.apply_field_to_all(field="newest_id", value=None, collection=DB.MP_COLLECTION)
    # db_connection.apply_field_to_all(field="oldest_id", value=None, collection=DB.MP_COLLECTION)
    # db_connection.apply_field_to_all(field="tweets_collected", value=0, collection=DB.MP_COLLECTION)

#
#
# db_connection = DBConnection()
# # db_connection.apply_field_to_all(field="newest_id", value=None, collection=DB.MP_COLLECTION)
# # db_connection.apply_field_to_all(field="oldest_id", value=None, collection=DB.MP_COLLECTION)
# # db_connection.apply_field_to_all(field="tweets_collected", value=0, collection=DB.MP_COLLECTION)
#
# twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
#                       os.environ.get(CREDS.TWITTER_SECRET),
#                       os.environ.get(CREDS.TWITTER_TOKEN),
#                       os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
#                       db_connection)
#
# twitter_api.get_trends(globally=True)
# #
# # # twitter_api.get_previous_tweets(mp_doc=db_connection.find_document(collection=DB.MP_COLLECTION,
# # #                                                                    filter={"twitter_handle": "@theresa_may"},
# # #                                                                    projection={"twitter_handle": 1, "oldest_id": 1})[0])
# # # twitter_api.update_all_mps()
# #
# # mp_list = db_connection.find_document(collection=DB.MP_COLLECTION,
# #                                               filter={},
# #                                               projection={"twitter_handle": 1, "oldest_id": 1,
# #                                                           "newest_id": 1, "tweet_count": 1,
# #                                                           "tweets_collected": 1})
# #
# # for mp in mp_list:
# #     twitter_api.get_tweets(mp_doc=mp, historic=True)
# #
# # mp_list.close()  # Close cursor
# # twitter_api.update_all_tweets(historic=True)






