# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

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
    if 'mp_search' in request.GET:
        mp_name = request.GET['mp_search']
        mp_list = MemberParliament.objects.filter(name__contains=mp_name.title())
        return render(request, 'checkr_app/index.html', {'mp_list': mp_list})

    tweet_list = Tweet.objects.order_by("-retweet_count")[:10]
    # tweet = tweet_list[0] # for tweet in tweet_list:
    for tweet in tweet_list:
        if not tweet.html:
            html = twitter_api.get_embed(tweet.id)

    return render(request, 'checkr_app/index.html', {'tweet_list': tweet_list})


def view_mps(request):
    if 'mp_search' in request.GET:
        mp_name = request.GET['mp_search']
        mp_list = MemberParliament.objects.filter(name__contains=mp_name.title())
    else:
        mp_list = MemberParliament.objects.order_by("-followers_count")[:10]

    return render(request, 'checkr_app/index.html', {'mp_list': mp_list})


def view_mp(request, mp_id):
    mp_tweets = Tweet.objects.filter(author_id=mp_id).order_by("-id")[:20]
    mp = MemberParliament.objects.get(id=mp_id)
    for tweet in mp_tweets:
        if not tweet.html:
            html = twitter_api.get_embed(tweet.id)

    print mp.name

    return render(request, 'checkr_app/index.html', {'tweet_list': mp_tweets, 'mp': mp})


def autocompleteModel(request):
    search_qs = MemberParliament.objects.filter(name__startswith=request.REQUEST['search'])
    results = []
    for r in search_qs:
        results.append(r.name)
    resp = request.REQUEST['callback'] + '(' + json.dumps(results) + ');'
    return HttpResponse(resp, content_type='application/json')

