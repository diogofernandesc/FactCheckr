import twitter
from twitter import TwitterError
from db_engine import DBConnection
from cons import DB, CREDS
import os
import time
from datetime import datetime
import logging


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
            access_token_secret=self.access_token_secret
        )

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
            print "Twitter ID not found: %s" % user_id
            return {}  #Twitter handle doesn't exist

        if data.status: # This MP has tweeted
            user_dict = {
                'description': data.description,
                'followers_count': data.followers_count,
                'tweet_count': data.statuses_count,
                'newest_id': data.status.id,
                'oldest_id': data.status.id
            }

            self.db_connection.update_mp(data.id, user_dict)

        else:
            print "MP: %s - has not tweeted" % user_id

    def new_mp(self, twitter_handle):
        try:
            data = self.api.GetUser(screen_name=twitter_handle)
        except:
            print "Twitter handle not found: %s" % twitter_handle
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
                if oldest_id or newest_id:
                    if historic:
                        tweets = self.api.GetUserTimeline(user_id=user_id,
                                                          count=200,
                                                          exclude_replies=False,
                                                          include_rts=False,
                                                          max_id=oldest_id,
                                                          trim_user=True
                                                          )
                    else:
                        tweets = self.api.GetUserTimeline(user_id=user_id,
                                                          count=200,
                                                          exclude_replies=False,
                                                          include_rts=False,
                                                          since_id=newest_id,
                                                          trim_user=True
                                                          )
                else:
                    break
            except TwitterError:
                self.logger.debug("Rate limit for twitter reached.. now sleeping")
                time.sleep(60 * 16)
                self.get_update_tweets(mp_doc=mp_doc, historic=historic)
                break

            if tweets:
                calls_to_api += 1
                if not old_tweets == tweets:
                    tweet_list = []
                    similar_count = 0  # Track how many of the same tweets have appeared
                    for tweet in tweets:
                        if historic:
                            if tweet.id < oldest_id:
                                oldest_id = tweet.id

                            elif tweet.id == oldest_id:
                                similar_count += 1
                                if similar_count == 2:
                                    tweets_available = False
                                    break

                            else:
                                break

                        else:
                            if tweet.id > newest_id:
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

                        # self.db_connection.insert_tweet(formatted_tweet)
                        tweet_list.append(formatted_tweet)

                    old_tweets = tweets
                    self.db_connection.insert_tweets(tweet_list)  # Insert in batches of 200 (if there are 200 new tweets)
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
        total_calls_to_api = 0
        mp_list = db_connection.find_document(collection=DB.MP_COLLECTION,
                                              filter={},
                                              projection={"twitter_handle": 1, "oldest_id": 1, "newest_id": 1})
        for mp in mp_list:
            self.logger.info("Updating ALL tweets for: %s" % mp["twitter_handle"])
            total_calls_to_api += self.get_update_tweets(mp_doc=mp, historic=historic)
            if total_calls_to_api % 850 == 0:
                self.logger.info("Sleeping to control Twitter rate limit")
                time.sleep(60 * 16)


db_connection = DBConnection()
twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
                      os.environ.get(CREDS.TWITTER_SECRET),
                      os.environ.get(CREDS.TWITTER_TOKEN),
                      os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
                      db_connection)

# twitter_api.get_previous_tweets(mp_doc=db_connection.find_document(collection=DB.MP_COLLECTION,
#                                                                    filter={"twitter_handle": "@theresa_may"},
#                                                                    projection={"twitter_handle": 1, "oldest_id": 1})[0])
# twitter_api.update_all_mps()
twitter_api.update_all_tweets(historic=True)






