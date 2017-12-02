import twitter


class Twitter(object):
    def __init__(self, consumer_key, consumer_secret, access_token_key, access_token_secret):
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

    def get_timeline(self, user):
        tweets = self.api.GetUserTimeline(screen_name=user,
                                            count=200,
                                            exclude_replies=True,
                                            include_rts=False)
        print tweets[0]


def get_twitter_credentials():
    with open("creds.txt", "r") as creds:
        for line in creds:
            if line.startswith("!twitter"):
                twitter_credentials = line.split("-->")[1].split(",")
                return twitter_credentials

tc = get_twitter_credentials()
twitter_api = Twitter(tc[0], tc[1], tc[2], tc[3])
twitter_api.get_timeline("theresa_may")
