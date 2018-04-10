class DB(object):
    NAME = "ip_db"
    TWEET_COLLECTION = "mp_tweets"
    RETWEET_COLLECTION = "mp_retweets"
    MP_COLLECTION = "mp_data"
    NEWS_ARTICLES = 'news_articles'
    SOURCES_COLLECTION = "news_sources"
    TWITTER_TRENDS = "twitter_trends"
    WIKI_TRENDS = "wiki_trends"


class NEWS_ARTICLE(object):
    DESCRIPTION = "description"
    TITLE = "title"
    URL = "url"
    SOURCE = "source"
    PUBLISH_DATE = "published_at"
    CATEGORY = "category"
    TIMESTAMP = "timestamp"


class NEWS_SOURCE(object):
    CATEGORY = 'category'
    DESCRIPTION = 'description'
    LANGUAGE = 'language'
    URL = 'url'
    COUNTRY = 'country'
    NAME = 'name'
    NEWS_API_ID = 'news_api_id'
    NEWS_API_FRIENDLY = 'news_api_friendly'  # Is it used by NEWS API


class NEWS_CATEGORIES(object):
    BUSINESS = "business"
    ENTERTAINMENT = "entertainment"
    GENERAL = "general"
    HEALTH = "health"
    SCIENCE = "science"
    SPORTS = "sports"
    TECHNOLOGY = "technology"


class NEWS_COUNTRIES(object):
    USA = 'us'
    UK = 'gb'


class NEWS_API_PARAMS(object):
    ENGLISH = 'en'
    SORT_BY_RELEVANCY = 'relevancy'
    SORT_BY_POPULARITY = 'popularity'
    SORT_BY_NEWEST = 'publishedAt'
    PAGE_SIZE = 100  # Default is 20 for API, gets max=100
    SOURCE = 'sources'

class WIKI_SOURCES(object):
    ENGLISH_WIKIPEDIA = "en.wikipedia"


class WIKI_TREND(object):
    NAME = "name"
    RANK = "rank"
    VIEWS = "views"
    DATE_STRING = "nice_date"
    DATE_OBJECT = "date"
    TIMESTAMP = "epoch_timestamp"
    MONTH = "month"
    WEEKDAY = "week_day"
    MONTH_DAY = "month_day"
    YEAR = "year"


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


class WOEIDS(object):
    UK = 23424975
    USA = 23424977


class TWITTER_TREND(object):
    NAME = "name"
    TWEET_VOLUME = "tweet_volume"
    URL = "url"
    TIMESTAMP = "timestamp"
    TIMESTAMP_EPOCH = "timestamp_epoch"
    LOCATION = "location"


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
    LINKS = "links"


class CREDS(object):
    TWITTER_KEY = "TWITTER_KEY"
    TWITTER_SECRET = "TWITTER_SECRET"
    TWITTER_TOKEN = "TWITTER_TOKEN"
    TWITTER_TOKEN_SECRET = "TWITTER_TOKEN_SECRET"


class CROWDFLOWER(object):
    TWEET_CONTENT = 'tweet_content'
    ENTITY_LIST = 'entity_list'


