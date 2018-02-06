class DB(object):
    NAME = "ip_db"
    TWEET_COLLECTION = "mp_tweets"
    RETWEET_COLLECTION = "mp_retweets"
    MP_COLLECTION = "mp_data"
    NEWS_COLLECTION = 'news_headlines'


class NEWS_HEADLINE(object):
    DESCRIPTION = "description"
    TITLE = "title"
    URL = "url"
    AUTHOR = "author"
    PUBLISH_DATE = "published_at"
    CATEGORY = "category"

class NEWS_CATEGORIES(object):
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    GENERAL = "general"
    HEALTH = "health"
    SCIENCE = "science"
    SPORTS = "sports"
    TECHNOLOGY = "technology"



class CREDS(object):
    TWITTER_KEY = "TWITTER_KEY"
    TWITTER_SECRET = "TWITTER_SECRET"
    TWITTER_TOKEN = "TWITTER_TOKEN"
    TWITTER_TOKEN_SECRET = "TWITTER_TOKEN_SECRET"
