import twitter
from db_engine import DBConnection
from cons import DB, CREDS
import os
import time
from datetime import datetime


class Twitter(object):
    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret, db_connection):
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
        print tweets[0]

    def get_user_data(self, user_id):
        try:
            data = self.api.GetUser(user_id=user_id)
            print data
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

    def get_previous_tweets(self, mp_doc):
        '''

        :param mp_doc: Document for mp returned from find projection
        :return: A list of dicts representing a tweet each pushed to DB
        '''

        user_id = mp_doc["_id"]
        oldest_id = mp_doc["oldest_id"]
        twitter_handle = mp_doc["twitter_handle"]


        tweets = self.api.GetUserTimeline(user_id=user_id,
                                          count=1,
                                          exclude_replies=False,
                                          include_rts=False,
                                          max_id=oldest_id,
                                          trim_user=True
                                          )
        if tweets:
            tweet_list = []
            for tweet in tweets:
                if tweet.id < oldest_id:
                    oldest_id = tweet.id

                if tweet.urls:
                    url = tweet.urls[0].url

                formatted_tweet = {
                    "_id": tweet.id,
                    "text": tweet.text,
                    "author_id": user_id,
                    "author_handle": twitter_handle,
                    "favourite_count": tweet.favorite_count,
                    "retweet_count": tweet.retweet_count,
                    "url": url,
                }

                # Sun May 21 17:36:44 +0000 2017
                date = datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')
                # date = time.strftime('%Y-%m-%d %H:%M:%S',
                #                      time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y'))
                formatted_tweet["created_at"] = date

                hashtags = []
                for hashtag in tweet.hashtags:
                    hashtags.append(hashtag.text)

                if hashtags:
                    formatted_tweet["hashtags"] = hashtags

                tweet_list.append(formatted_tweet)

            self.db_connection.insert_tweets(tweet_list)

        while tweets:
            tweets = self.api.GetUserTimeline(user_id=user_id,
                                              count=200,
                                              exclude_replies=False,
                                              include_rts=False,
                                              max_id=oldest_id,
                                              trim_user=True,
                                              )

            if tweets:
                tweet_list = []
                for tweet in tweets:
                    if tweet.id < oldest_id:
                        oldest_id = tweet.id

                    if tweet.urls:
                        url = tweet.urls[0].url

                    formatted_tweet = {
                        "_id": tweet.id,
                        "text": tweet.text,
                        "author_id": user_id,
                        "author_handle": twitter_handle,
                        "favourite_count": tweet.favorite_count,
                        "retweet_count": tweet.retweet_count,
                        "url": url,
                    }

                    # Sun May 21 17:36:44 +0000 2017
                    date = datetime.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y')
                    # date = time.strftime('%Y-%m-%d %H:%M:%S',
                    #                      time.strptime(tweet.created_at, '%a %b %d %H:%M:%S +0000 %Y'))
                    formatted_tweet["created_at"] = date

                    hashtags = []
                    for hashtag in tweet.hashtags:
                        hashtags.append(hashtag.text)

                    if hashtags:
                        formatted_tweet["hashtags"] = hashtags

                    tweet_list.append(formatted_tweet)

                self.db_connection.insert_tweets(tweet_list)

        self.db_connection.update_mp(user_id=user_id, update={"$set": {"oldest_id": oldest_id}})


def update_all_mps():
    for mp in db_connection.find_document(collection=DB.MP_COLLECTION,
                                          filter={"newest_id": {"$exists": True}},
                                          projection={"oldest_id": 1}):
        twitter_api.get_user_data(mp["_id"])


db_connection = DBConnection()
twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
                      os.environ.get(CREDS.TWITTER_SECRET),
                      os.environ.get(CREDS.TWITTER_TOKEN),
                      os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
                      db_connection)

twitter_api.get_previous_tweets(mp_doc=db_connection.find_document(collection=DB.MP_COLLECTION,
                                                                   filter={"twitter_handle": "@theresa_may"},
                                                                   projection={"twitter_handle":1, "oldest_id": 1})[0])







