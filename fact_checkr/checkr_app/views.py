# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from bson.objectid import ObjectId
from django.http import HttpResponse
from ingest_engine.twitter_ingest import Twitter
from cons import CREDS
from db_engine import DBConnection
from django.shortcuts import render
from .models import MemberParliament, Tweet
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
db_connection = DBConnection()
twitter_api = Twitter(os.environ.get(CREDS.TWITTER_KEY),
                          os.environ.get(CREDS.TWITTER_SECRET),
                          os.environ.get(CREDS.TWITTER_TOKEN),
                          os.environ.get(CREDS.TWITTER_TOKEN_SECRET),
                          db_connection)


def index(request):
    tweet_list = Tweet.objects.order_by("-retweet_count")[:10]
    # tweet = tweet_list[0] # for tweet in tweet_list:
    for tweet in tweet_list:
        if not tweet.html:
            html = twitter_api.get_embed(tweet.id)

    return render(request, 'checkr_app/index.html', {'tweet_list': tweet_list})
