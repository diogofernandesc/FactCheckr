import twitter
from db_engine import DBConnection
from cons import DB, CREDS
import os


class Twitter(object):
    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret):
        # self.db_connection = db_connection
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
            }

            # self.db_connection.update_mp(data.id, user_dict)

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
        # self.db_connection.create_mp(user_dict)


#
#
# def get_twitter_credentials():
#     with open("creds.txt", "r") as creds:
#         for line in creds:
#             if line.startswith("!twitter"):
#                 twitter_credentials = line.split("-->")[1].split(",")
#                 return twitter_credentials


# tc = get_twitter_credentials()
# db_connection = DBConnection()
# twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
#                       os.environ.get(CREDS.TWITTER_SECRET),
#                       os.environ.get(CREDS.TWITTER_TOKEN),
#                       os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
#                       db_connection)


