# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import division

import json

from bson.objectid import ObjectId
from django.http import HttpResponse
from ingest_engine.twitter_ingest import Twitter
from cons import CREDS, DB, TWEET, MP
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
        mp_list = db_connection.find_document(collection=DB.MP_COLLECTION,
                                              filter={"name": {"$regex": mp_name.title()}})
    # if 'mp_search' in request.GET:
    #     mp_name = request.GET['mp_search']
    #     mp_list = MemberParliament.objects.filter(name__contains=mp_name.title())
        # mp_list = db_connection.find_document(collection=DB.MP_COLLECTION,
                                              # filter={"name": {"$regex": mp_name}})

        mp_list = list(mp_list)
        for mp in mp_list:
            mp["id"] = mp[MP.ID]
            if MP.FACTUAL_SCORE in mp:
                mp[MP.FACTUAL_SCORE] = round(mp[MP.FACTUAL_SCORE] / mp[MP.NO_FACT_CHECKED_TWEETS], 4) * 100
        return render(request, 'checkr_app/index.html', {'mp_list': mp_list})

    # tweet_list = Tweet.objects.order_by("-retweet_count")[1:10]
    tweet_list = db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                             filter={TWEET.CONFIDENCE_SCORE: {"$exists": True}},
                                             projection={TWEET.CONFIDENCE_SCORE: 1, TWEET.HTML: 1,
                                                         TWEET.PREDICTED_VERDICT: 1}
                                             )
    tweet_list = list(tweet_list)
    for tweet in tweet_list:
        tweet[TWEET.CONFIDENCE_SCORE] = round(tweet[TWEET.CONFIDENCE_SCORE] * 100, 2)
    # tweet_list = Tweet.objects.filter()[:10]
    # tweet = tweet_list[0] # for tweet in tweet_list:
    for tweet in tweet_list:
        if "html" not in tweet:
            html = twitter_api.get_embed(tweet[TWEET.ID])

    return render(request, 'checkr_app/index.html', {'tweet_list': tweet_list})


def view_mps(request):
    if 'mp_search' in request.GET:
        mp_name = request.GET['mp_search']
        mp_list = db_connection.find_document(collection=DB.MP_COLLECTION,
                                              filter={"name": {"$regex": mp_name}})

        # mp_list = MemberParliament.objects.filter(name__contains=mp_name.title())
    else:
        mp_list = db_connection.find_document(collection=DB.MP_COLLECTION, filter={},
                                              projection={MP.NO_FACT_CHECKED_TWEETS: 1,
                                                          MP.FACTUAL_SCORE: 1,
                                                          MP.TWEET_COUNT: 1,
                                                          MP.FRIENDS_COUNT: 1,
                                                          MP.FOLLOWERS_COUNT: 1,
                                                          MP.TWITTER_HANDLE: 1,
                                                          MP.NAME: 1,
                                                          MP.PARTY:1,
                                                          MP.CONSTITUENCY: 1,
                                                          })
        # mp_list = MemberParliament.objects.order_by("-followers_count")[:10]

    mp_list = list(mp_list)
    for mp in mp_list:
        mp["id"] = mp[MP.ID]
        if MP.FACTUAL_SCORE in mp:
            mp[MP.FACTUAL_SCORE] = round(mp[MP.FACTUAL_SCORE] / mp[MP.NO_FACT_CHECKED_TWEETS], 4) * 100
    return render(request, 'checkr_app/index.html', {'mp_list': mp_list})


def view_mp(request, mp_id):
    if 'mp_search' in request.GET:
        mp_name = request.GET['mp_search']
        mp_list = db_connection.find_document(collection=DB.MP_COLLECTION,
                                              filter={"name": {"$regex": mp_name.title()}})
    # if 'mp_search' in request.GET:
    #     mp_name = request.GET['mp_search']
    #     mp_list = MemberParliament.objects.filter(name__contains=mp_name.title())
        # mp_list = db_connection.find_document(collection=DB.MP_COLLECTION,
                                              # filter={"name": {"$regex": mp_name}})

        mp_list = list(mp_list)
        for mp in mp_list:
            mp["id"] = mp[MP.ID]
            if MP.FACTUAL_SCORE in mp:
                mp[MP.FACTUAL_SCORE] = round(mp[MP.FACTUAL_SCORE] / mp[MP.NO_FACT_CHECKED_TWEETS], 4) * 100
        return render(request, 'checkr_app/index.html', {'mp_list': mp_list})

    mp_tweets = db_connection.find_document(collection=DB.RELEVANT_TWEET_COLLECTION,
                                             filter={"$and": [{TWEET.CONFIDENCE_SCORE: {"$exists": True}},
                                                              {TWEET.AUTHOR_ID: int(mp_id)}]})
    mp_tweets = list(mp_tweets)
    for tweet in mp_tweets:
        tweet[TWEET.CONFIDENCE_SCORE] = round(tweet[TWEET.CONFIDENCE_SCORE] * 100, 2)

    mp = db_connection.find_document(collection=DB.MP_COLLECTION, filter={MP.ID: int(mp_id)})
    if mp.count() > 0:
        mp = list(mp)[0]
        if MP.FACTUAL_SCORE in mp:
            mp[MP.FACTUAL_SCORE] = round(mp[MP.FACTUAL_SCORE] / mp[MP.NO_FACT_CHECKED_TWEETS], 4) * 100

    # mp_tweets = Tweet.objects.filter(author_id=mp_id).order_by("-id")[:20]
    # mp = MemberParliament.objects.get(id=mp_id)
    for tweet in mp_tweets:
        if "html" not in tweet:
            html = twitter_api.get_embed(tweet[TWEET.ID])

    # print mp.name

    return render(request, 'checkr_app/index.html', {'tweet_list': mp_tweets, 'mp': mp})


# def autocompleteModel(request):
#     search_qs = MemberParliament.objects.filter(name__startswith=request.REQUEST['search'])
#     results = []
#     for r in search_qs:
#         results.append(r.name)
#     resp = request.REQUEST['callback'] + '(' + json.dumps(results) + ');'
#     return HttpResponse(resp, content_type='application/json')