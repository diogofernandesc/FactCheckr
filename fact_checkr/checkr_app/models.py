# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from djangotoolbox.fields import ListField


class MemberParliament(models.Model):
    id = models.BigIntegerField(primary_key=True)
    twitter_handle = models.CharField(max_length=200)
    description = models.TextField()
    followers_count = models.IntegerField()
    party = models.CharField(max_length=200)
    constituency = models.CharField(max_length=200)
    tweet_count = models.IntegerField()
    name = models.CharField(max_length=200)
    newest_id = models.IntegerField(null=True)
    oldest_id = models.IntegerField()
    tweets_collected = models.IntegerField()

    class MongoMeta:
        db_table = "mp_data"

class Tweet(models.Model):
    id = models.BigIntegerField(primary_key=True)
    retweet_count = models.IntegerField()
    favourites_count = models.IntegerField()
    links = ListField()
    url = models.CharField(max_length=200)
    text = models.TextField()
    created_at = models.DateTimeField()
    hashtags = ListField()
    author_handle = models.CharField(max_length=200)
    last_updated = models.DateTimeField()
    author_id = models.IntegerField()
    created_at_epoch = models.IntegerField()
    html = models.TextField()

    class MongoMeta:
        db_table = "mp_tweets"
