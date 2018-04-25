class DB(object):
    NAME = "ip_db"
    TWEET_COLLECTION = "mp_tweets"
    RELEVANT_TWEET_COLLECTION = "relevant_mp_tweets"
    RETWEET_COLLECTION = "mp_retweets"
    MP_COLLECTION = "mp_data"
    NEWS_ARTICLES = 'news_articles'
    SOURCES_COLLECTION = "news_sources"
    TWITTER_TRENDS = "twitter_trends"
    WIKI_TRENDS = "wiki_trends"
    TOP_NEWS_DOMAINS = "top_news_domains"
    RELEVANT_TOPICS = "relevant_topics"


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
    FRIENDS_COUNT = "friends_count"
    PARTY = "party"
    CONSTITUENCY = "constituency"
    TWEET_COUNT = "tweet_count"
    NAME = "name"
    TOPICS_OF_INTEREST = "topics_of_interest"
    TWEETS_COLLECTED = "tweets_collected"
    IS_VERIFIED = "is_verified"
    AVERAGE_NO_RETWEETS = "average_no_retweets"
    AVERAGE_NO_FAVOURITES = "average_no_favourites"
    NON_EMPTY_DESCRIPTION = "non_empty_description"
    ACCOUNT_DAYS = "account_days"
    TOPICS = "topics"
    CREATED_AT = "created_at"
    CREATED_AT_EPOCH = "created_at_epoch"


class TOPIC(object):
    IDENTIFIED_AS_TOPIC = "identified_as_topic" # Number of times it was identified as topic
    TWEET_COUNT = "tweet_count"
    TWEET_AVERAGE_LENGTH = "average_length"
    FRAC_CONTAINING_QM = "frac_containing_qm"
    FRAC_CONTAINING_EM = "frac_containing_em"
    FRAC_CONTAINING_MULTIPLE_MARKS = "frac_containing_multiple_marks"
    FRAC_CONTAINING_HAPPY_EMOTICON = "frac_containing_happy_emoticon"
    FRAC_CONTAINING_SAD_EMOTICON = "frac_containing_sad_emoticon"
    FRAC_CONTAINING_HAPPY_EMOJI = "frac_containing_happy_emoji"
    FRAC_CONTAINING_SAD_EMOJI = "frac_containing_sad_emoji"
    FRAC_CONTAINING_PRONOUNS = "frac_containing_pronouns"
    FRAC_CONTAINING_UPPERCASE = "frac_containing_uppercase"
    FRAC_CONTAINING_URL = "frac_containing_url"
    FRAC_CONTAINING_USER_MENTION = "frac_containing_user_mention"
    FRAC_CONTAINING_HASHTAGS = "frac_containing_hashtags"
    FRAC_CONTAINING_STOCK_SYMBOLS = "frac_containing_stock_symbols"
    AVERAGE_SENTIMENT_SCORE = "avg_sentiment_score"
    FRAC_CONTAINING_POSITIVE_SENTIMENT = "frac_containing_positive_sentiment"
    FRAC_CONTAINING_NEGATIVE_SENTIMENT = "frac_containing_negative_sentiment"
    FRAC_CONTAINING_DOMAIN10 = "frac_containing_domain10"
    FRAC_CONTAINING_DOMAIN30 = "frac_containing_domain30"
    FRAC_CONTAINING_DOMAIN50 = "frac_containing_domain50"
    DISTINCT_URLS_COUNT = "distinct_urls_count"
    FRAC_CONTAINING_MOST_VISITED_URL = "frac_containing_top_url"
    DISTINCT_HASHTAG_COUNT = "distinct_hashtag_count"
    FRAC_CONTAINING_MOST_USED_HASHTAG = "frac_containing_top_hashtag"
    DISTINCT_USER_MENTION_COUNT = "distinct_user_mention_count"
    FRAC_CONTAINING_MOST_MENTIONED_USER = "frac_containing_top_mentioned_user"
    DISTINCT_TWEET_AUTHOR_COUNT = "distinct_tweet_author_count"
    FRAC_CONTAINING_TOP_AUTHOR = "frac_containing_top_author"
    AVERAGE_AUTHOR_TWITTER_LIFE = "avg_author_life"
    AVERAGE_AUTHOR_TWEET_COUNT = "avg_author_tweet_count"
    AVERAGE_AUTHOR_FOLLOWER_COUNT = "avg_author_follower_count"
    AVERAGE_AUTHOR_FRIEND_COUNT = "avg_author_friend_count"
    FRAC_FROM_VERIFIED = "frac_from_verified"
    AVERAGE_DAY_RELEVANCE = "avg_day_relevance"
    AVERAGE_WEEK_RELEVANCE = "avg_week_relevance"
    AVERAGE_2WEEK_RELEVANCE = "avg_2week_relevance"



class DOMAIN(object):
    URL = "url"
    RANK = "rank"
    NAME = "name"

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
    KEYWORDS = "keywords"
    ENTITIES = "entities"
    CHARACTER_COUNT = "character_count"
    WORD_COUNT = "word_count"
    CONTAINS_QM = "contains_qm"
    CONTAINS_EM = "contains_em"
    CONTAINS_MULTIPLE_MARKS = "contains_multiple_m"
    FRACTION_CAPITALISED = "frac_capitalised"
    CONTAINS_HAPPY_EMOJI = "contains_happy_emoji"
    CONTAINS_SAD_EMOJI = "contains_sad_emoji"
    CONTAINS_HAPPY_EMOTICON = "contains_happy_emoticon"
    CONTAINS_SAD_EMOTICON = "contains_sad_emoticon"
    CONTAINS_PRONOUNS = "contains_pronouns"
    CONTAINS_DOMAIN_TOP10 = "contains_domain_top10"
    CONTAINS_DOMAIN_TOP30 = "contains_domain_top30"
    CONTAINS_DOMAIN_TOP50 = "contains_domain_top50"
    MENTIONED_USERS = "mentioned_users"
    MENTIONS_USER = "mentions_user"
    CONTAINS_STOCK_SYMBOL = "contains_stock_symbol"
    PUBLISH_WEEKDAY = "publish_weekday"
    POSITIVE_WORD_COUNT = "positive_word_count"
    NEGATIVE_WORD_COUNT = "negative_word_count"
    SENTIMENT_SCORE = "sentiment_score"
    AVERAGE_ENTITY_CERTAINTY = "avg_entity_certainty"
    AVERAGE_KEYWORD_CERTAINTY = "avg_keyword_certainty"
    ENTITIES_COUNT = "entities_count"
    KEYWORDS_COUNT = "keywords_count"
    RELEVANCY_DAY = 'relevancy_day'
    RELEVANCY_WEEK = 'relevancy_week'
    RELEVANCY_TWO_WEEKS = 'relevancy_2weeks'
    SET_TO_FACTCHECK = "set_to_factcheck"  # has been crowdsourced/analysed and decision made = True/False
    LABEL = "label"
    VERIFIED_URLS = "verified_urls_real"
    CONTAINS_FIGURES = 'contains_figures'
    FRAC_NOT_IN_DICT = 'frac_not_in_dict'


class CREDS(object):
    TWITTER_KEY = "TWITTER_KEY"
    TWITTER_SECRET = "TWITTER_SECRET"
    TWITTER_TOKEN = "TWITTER_TOKEN"
    TWITTER_TOKEN_SECRET = "TWITTER_TOKEN_SECRET"


class CROWDFLOWER(object):
    TWEET_CONTENT = 'tweet_content'
    ENTITY_LIST = 'entity_list'
    FACTCHECKABLE_ANSWERS = "tick_the_box_of_the_tweets_that_are_politically_important_andor_worth_factchecking"
    TWEET_LIST = "tweet_list"


class CLASSIFIER(object):
    ALMOST_DEFINITELY_TRUE = 1
    LIKELY_TO_BE_FALSE = -1
    ALMOST_DEFINITELY_FALSE = -1

class TIME_INTERVAL(object):
    DAY = 86400
    WEEK = 604800
    MONTH = 2629746


class RELEVANCY_INTERVAL(object):
    DAY = 'relevancy_day'
    WEEK = 'relevancy_week'
    TWO_WEEKS = 'relevancy_2weeks'
    MONTH = 'relevancy_month'


class WEEKDAY(object):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


HAPPY_EMOJI = {
    u':cat_face_with_wry_smile:': u'\U0001F63C',
    u':cat_face_with_tears_of_joy:': u'\U0001F639',
    u':grimacing_face:': u'\U0001F62C',
    u':grinning_cat_face:': u'\U0001F63A',
    u':grinning_cat_face_with_smiling_eyes:': u'\U0001F638',
    u':grinning_face:': u'\U0001F600',
    u':grinning_face_with_big_eyes:': u'\U0001F603',
    u':grinning_face_with_smiling_eyes:': u'\U0001F604',
    u':grinning_face_with_sweat:': u'\U0001F605',
    u':grinning_squinting_face:': u'\U0001F606',
    u':kissing_face_with_smiling_eyes:': u'\U0001F619',
    u':slightly_smiling_face:': u'\U0001F642',
    u':smiling_cat_face_with_heart-eyes:': u'\U0001F63B',
    u':smiling_face:': u'\U0000263A',
    u':smiling_face_with_halo:': u'\U0001F607',
    u':smiling_face_with_heart-eyes:': u'\U0001F60D',
    u':smiling_face_with_horns:': u'\U0001F608',
    u':smiling_face_with_smiling_eyes:': u'\U0001F60A',
    u':smiling_face_with_sunglasses:': u'\U0001F60E',
    u':smirking_face:': u'\U0001F60F',
    u':beaming_face_with_smiling_eyes:': u'\U0001F601',
}

UNHAPPY_EMOJI = {
    u':man_frowning:': u'\U0001F64D\U0000200D\U00002642\U0000FE0F',
    u':man_frowning_dark_skin_tone:': u'\U0001F64D\U0001F3FF\U0000200D\U00002642\U0000FE0F',
    u':man_frowning_light_skin_tone:': u'\U0001F64D\U0001F3FB\U0000200D\U00002642\U0000FE0F',
    u':man_frowning_medium-dark_skin_tone:': u'\U0001F64D\U0001F3FE\U0000200D\U00002642\U0000FE0F',
    u':man_frowning_medium-light_skin_tone:': u'\U0001F64D\U0001F3FC\U0000200D\U00002642\U0000FE0F',
    u':man_frowning_medium_skin_tone:': u'\U0001F64D\U0001F3FD\U0000200D\U00002642\U0000FE0F',
    u':person_frowning:': u'\U0001F64D',
    u':person_frowning_dark_skin_tone:': u'\U0001F64D\U0001F3FF',
    u':person_frowning_light_skin_tone:': u'\U0001F64D\U0001F3FB',
    u':person_frowning_medium-dark_skin_tone:': u'\U0001F64D\U0001F3FE',
    u':person_frowning_medium-light_skin_tone:': u'\U0001F64D\U0001F3FC',
    u':person_frowning_medium_skin_tone:': u'\U0001F64D\U0001F3FD',
    u':slightly_frowning_face:': u'\U0001F641',
    u':woman_frowning:': u'\U0001F64D\U0000200D\U00002640\U0000FE0F',
    u':woman_frowning_dark_skin_tone:': u'\U0001F64D\U0001F3FF\U0000200D\U00002640\U0000FE0F',
    u':woman_frowning_light_skin_tone:': u'\U0001F64D\U0001F3FB\U0000200D\U00002640\U0000FE0F',
    u':woman_frowning_medium-dark_skin_tone:': u'\U0001F64D\U0001F3FE\U0000200D\U00002640\U0000FE0F',
    u':woman_frowning_medium-light_skin_tone:': u'\U0001F64D\U0001F3FC\U0000200D\U00002640\U0000FE0F',
    u':woman_frowning_medium_skin_tone:': u'\U0001F64D\U0001F3FD\U0000200D\U00002640\U0000FE0F',
    u':frowning_face:': u'\U00002639',
    u':frowning_face_with_open_mouth:': u'\U0001F626',
}

EMOJI_HAPPY = {v: k for k, v in HAPPY_EMOJI.items()}
EMOJI_UNHAPPY = {v: k for k, v in UNHAPPY_EMOJI.items()}
