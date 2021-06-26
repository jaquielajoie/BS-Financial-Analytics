import tweepy
from tweepy import API
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import Stream
from local_config import *
import json
from collections import Counter
import math
import time

"""
Returns a new Tweepy authentication instance
"""
def authenticate_twitter():
    auth = tweepy.OAuthHandler(cons_tok, cons_sec)
    auth.set_access_token(app_tok, app_sec)
    return auth

"""
Streams and processes live tweet data
"""
def stream_tweets(tweet_filepath, search_list):
    # tweet_filpath: where to save the tweets
    listener = TwitterListener(tweet_filepath=tweet_filepath)
    auth = authenticate_twitter()

    stream = Stream(auth, listener)
    stream.filter(track=search_list)

def check_decay(decay):
    if decay >= 1: # should this be increased over 1??
        return 1
    elif decay <= 0:
        return 0
    else:
        return decay

"""
This function attempts to recusively explore a search_term social network

Count: how many friends to observe
Decay is the amount to reduce spread by: must be between -1 and 1. 1 stops the recursion.
"""
def spread_search(screen_name, search_term, count, decay):

    tc = TwitterClient(screen_name=screen_name)
    friends = tc.grab_friends(count=count)
    count = math.ceil(count)

    if count < 1:
        return

    for friend in friends:
        """
        This function hits the rate limit
        """
        time.sleep(5)

        tc_friend = tc.change_name(friend._json['screen_name'])
        tweets = tc_friend.grab_tweets(count=count) # should this count be changed?

        for t in tweets:

            if t._json['text']: # contains the search_term
                decay += 0.01
            else:
                decay -= 0.01

            decay = check_decay(decay)

        count *= decay
        count = math.ceil(count)

        spread_search(screen_name=tc.screen_name, search_term=search_term, count=count, decay=decay)
        print(f'spread_search saw: {tc.screen_name} with a decay {decay} and count {count}')

class TwitterClient():

    def __init__(self, screen_name=None):
        self.auth = authenticate_twitter()
        self.client = API(self.auth)
        self.screen_name = screen_name

    def change_name(self, screen_name):
        self.screen_name = screen_name
        return self # returns a copy of existing TwitterClient - does this avoid extra API pings?

    def grab_tweets(self, count): # these are the tweets a screen_name has created
        tweets = []
        c = Cursor(self.client.user_timeline, id=self.screen_name).items(count)

        for tweet in c:
            tweets.append(tweet)

        return tweets

    """
    This refers to the people that the TwitterClient's screen_name follows
    """
    def grab_friends(self, count): # these are the friends a screen_name has
        friends = []
        c = Cursor(self.client.friends, id=self.screen_name).items(count)

        for friend in c:
            friends.append(friend)

        return friends

    """
    FIXME: this only grab's the TwitterClient's homeview
        id=self.screen_name has no effect
    """
    def grab_homeview(self, count): # these are the tweets a screen_name views on the "home" view
        tweets = []
        c = Cursor(self.client.home_timeline, id=self.screen_name).items(count)

        for tweet in c:
            tweets.append(tweet)

        return tweets


class TwitterListener(StreamListener):
    """
    Prints tweets to terminal & saves to json
    """
    def __init__(self, tweet_filepath):
        # tweet_filpath: where to save the tweets
        self.tweet_filepath = tweet_filepath

    def on_data(self, data):
        try:
            with open(self.tweet_filepath, 'a') as fp:
                fp.write(data)
            return True

        except BaseException as e:
            print(f'Error on_data: {e}')
            # return False

        return True

    def on_error(self, status):

        print(f'on_error | TwitterListener(StreamListener) | status == {status}')
        if status == 420:
            # returning False when Twitter API rate limit is hit
            return False


if __name__ == "__main__":

    # search_list = ['USDT', 'Tether']
    # tweet_filepath = 'tweets.json'

    spread_search(screen_name='pycon', search_term='python', count=2, decay=0.5)

    # tc = TwitterClient()

    # friends = tc.grab_friends(5)

    # for f in friends:
    #    print(f._json['screen_name'])
