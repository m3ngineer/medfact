import tweepy
import pandas as pd
import os
import json
import requests
import re
import matplotlib.pyplot as plt
import psycopg2
from dateutil import parser

class TweetExtractor():

    def __init__(self):
        self.consumer_key = os.environ["MF_TWITTER_CONSUMER_API_KEY"]
        self.consumer_secret = os.environ["MF_TWITTER_CONSUMER_API_KEY_SECRET"]
        self.access_token = os.environ["MF_TWITTER_ACCESS_TOKEN"]
        self.access_token_secret = os.environ["MF_TWITTER_ACCESS_TOKEN_SECRET"]
        self.api = self.authorize()
        self.db_name = os.environ['DB_NAME']
        self.db_user = os.environ['DB_USER']
        self.password = None
        self.db_host = 'localhost'

    def authorize(self):
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        api = tweepy.API(auth)

        return api

    def connect(self, tweet_id,
            created_at,
            tweet,
            in_reply_to_status_id,
            in_reply_to_user_id,
            in_reply_to_screen_name,
            geo,
            retweet_count,
            favorite_count,
            favorited,
            retweeted,
            user_id,
            username,
            screen_name,
            user_location,
            user_description,
            user_url,
            followers_count,
            friends_count,
            listed_count,
            user_favorites_count,
            statuses_count,
            user_lang):
        """ Connect to postgres database and insert Twitter data """

        try:
            conn = psycopg2.connect(host=self.db_host,
                                      dbname=self.db_name,
                                      user=self.db_user,
                                   )
            if conn.closed < 1:
                """ Insert Twitter data """
                cursor = conn.cursor()
                #Twitter, fold
                query = "INSERT INTO hcc_tweets (tweet_id, created_at, tweet, in_reply_to_status_id, in_reply_to_user_id, in_reply_to_screen_name, geo, retweet_count, favorite_count, favorited, retweeted, user_id, username, screen_name, user_location, user_description, user_url, followers_count, friends_count, listed_count, user_favorites_count, statuses_count, user_lang) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(query, (tweet_id, created_at, tweet, in_reply_to_status_id, in_reply_to_user_id, in_reply_to_screen_name, geo, retweet_count, favorite_count, favorited, retweeted, user_id, username, screen_name, user_location, user_description, user_url, followers_count, friends_count, listed_count, user_favorites_count, statuses_count, user_lang))
                conn.commit()

        except Exception as e:
            print('Unable to connect to database')
            print(e)

        cursor.close()
        conn.close()

        return

    def collect_tweet_data(self, query, max_tweets=10, cursor=0, wait=False):
        ''' Request tweet data and store in postgres database '''
        request = [status for status in tweepy.Cursor(self.api.search, q=query, tweet_mode='extended', cursor=cursor, wait_on_rate_limit=wait, wait_on_rate_limit_notify=True).items(max_tweets)]

        for status in request:
            if 'full_text' in status._json and status._json['full_text'].startswith('RT ') != True:
                data = status._json

                tweet_id = data['id']
                created_at = parser.parse(data['created_at'])
                tweet = data['full_text']
                in_reply_to_status_id = data['in_reply_to_status_id'],
                in_reply_to_user_id = data['in_reply_to_user_id'],
                in_reply_to_screen_name = data['in_reply_to_screen_name'],
                geo = data['geo'],
                retweet_count = data['retweet_count']
                favorite_count = data['favorite_count']
                favorited = data['favorited']
                retweeted = data['retweeted']
                user_id = data['user']['id']
                username = data['user']['name']
                screen_name = data['user']['screen_name']
                user_location = data['user']['location']
                user_description = data['user']['description']
                user_url = data['user']['url']
                followers_count = data['user']['followers_count']
                friends_count = data['user']['friends_count']
                listed_count = data['user']['listed_count']
                user_favorites_count = data['user']['favourites_count']
                statuses_count = data['user']['statuses_count']
                user_lang = data['user']['lang']

                self.connect(tweet_id,
                        created_at,
                        tweet,
                        in_reply_to_status_id,
                        in_reply_to_user_id,
                        in_reply_to_screen_name,
                        geo,
                        retweet_count,
                        favorite_count,
                        favorited,
                        retweeted,
                        user_id,
                        username,
                        screen_name,
                        user_location,
                        user_description,
                        user_url,
                        followers_count,
                        friends_count,
                        listed_count,
                        user_favorites_count,
                        statuses_count,
                        user_lang)

        return

if __name__ == "__main__":

    search_terms = ['liver chemo',
                'liver chemotherapy',
                'liver cancer',
                'liver cancer opdivo',
                'liver cancer keytruda',
                'hcc chemo',
                'hcc radiation',
                'hcc chemotherapy',
                'hepatocellular carcinoma',
               ]

    tweet_extractor = TweetExtractor()

    for term in search_terms:
        print('collecting tweets for "{}"...'.format(term))
        query = term
        tweet_extractor.collect_tweet_data(query, max_tweets=5000, wait=True)
