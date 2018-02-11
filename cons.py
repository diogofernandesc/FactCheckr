class DB(object):
    NAME = "ip_db"
    TWEET_COLLECTION = "mp_tweets2"
    RETWEET_COLLECTION = "mp_retweets2"
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


class MP(object):
    ID = "_id"
    OLDEST_ID = "oldest_id"
    NEWEST_ID = "newest_id"
    TWITTER_HANDLE = "twitter_handle"
    DESCRIPTION = "description"
    FOLLOWERS_COUNT = "followers_count"
    PARTY = "party"
    CONSTITUENCY = "constituency"
    TWEET_COUNT = "tweet_count"
    NAME = "name"
    TOPICS_OF_INTEREST = "topics_of_interest"
    TWEETS_COLLECTED = "tweets_collected"

class TWEET(object):
    ID = "_id"
    TEXT = "text"
    AUTHOR_ID = "author_id"
    AUTHOR_HANDLE = "author_handle"
    FAVOURITES_COUNT = "favourites_count"
    RETWEET_COUNT = "retweet_count"
    LAST_UPDATED = "last_updated"
    HASHTAGS = "hashtags"
    URL = "url"
    RETWEETER_HANDLE = "retweeter_handle"
    CREATED_AT = "created_at"
    CREATED_AT_EPOCH = "created_at_epoch"

class CREDS(object):
    TWITTER_KEY = "TWITTER_KEY"
    TWITTER_SECRET = "TWITTER_SECRET"
    TWITTER_TOKEN = "TWITTER_TOKEN"
    TWITTER_TOKEN_SECRET = "TWITTER_TOKEN_SECRET"
