import calendar
import sys
sys.path.append("..")
from python_twitter_fork import twitter
from python_twitter_fork.twitter import TwitterError
from db_engine import DBConnection
from cons import DB, CREDS, MP, TWEET, WOEIDS, TWITTER_TREND
import os
import time
from datetime import datetime
import logging
from requests import ConnectionError


logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))



class Twitter(object):
    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret, db_connection):
        self.logger = logging.getLogger(__name__)
        self.db_connection = db_connection
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token_key = access_token_key
        self.access_token_secret = access_token_secret
        self.api = twitter.Api(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token_key=self.access_token_key,
            access_token_secret=self.access_token_secret,
            sleep_on_rate_limit=True
        )

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
        if MP.OLDEST_ID in mp_doc:
            oldest_id = mp_doc[MP.OLDEST_ID]

        if MP.NEWEST_ID in mp_doc:
            newest_id = mp_doc[MP.NEWEST_ID]

        # Only collect tweets while the amount collected is less than the available for that MP
        while tweets_collected < tweet_count:
            raw_tweets = self.api.GetUserTimeline(user_id=user_id,
                                                  count=200,
                                                  exclude_replies=False,
                                                  include_rts=True,
                                                  since_id=newest_id,
                                                  max_id=oldest_id,
                                                  )

            if not raw_tweets:  # Break if API limit reached
                break

            tweets_collected += len(raw_tweets)
            for raw_tweet in raw_tweets:
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
                if raw_tweet.urls:
                    url = raw_tweet.urls[0].url
                    formatted_tweet[TWEET.URL] = url

                # Retweet handling
                if retweet:
                    formatted_tweet[TWEET.AUTHOR_HANDLE] = retweet_user
                    formatted_tweet[TWEET.RETWEETER_HANDLE] = twitter_handle
                    retweet_list.append(formatted_tweet)

                else:
                    tweet_list.append(formatted_tweet)

        if tweet_list:
            self.db_connection.insert_tweets(tweet_list)

        if retweet_list:
            self.db_connection.insert_tweets(tweet_list=retweet_list, retweets=True)

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
                    print tweets
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
        mp_list = db_connection.find_document(collection=DB.MP_COLLECTION,
                                              filter={},
                                              projection={"twitter_handle": 1, "oldest_id": 1, "newest_id": 1})
        for mp in mp_list:
            self.logger.info("Updating ALL tweets for: %s" % mp["twitter_handle"])
            self.get_tweets(mp_doc=mp, historic=historic)

        mp_list.close()


if __name__ == "__main__":
    db_connection = DBConnection()
    twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
                          os.environ.get(CREDS.TWITTER_SECRET),
                          os.environ.get(CREDS.TWITTER_TOKEN),
                          os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
                          db_connection)

    if "trends" in sys.argv:
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

            time.sleep(60*60*24)

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






