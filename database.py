# Database handler
import os
import dataset
import tweepy
import tweet_parser

class Database(object):
    '''
    Interacts with the database
    '''

    def __init__(self):
        self.db_url = os.environ.get("DATABASE_URL")
        if self.db_url is None:
            from keys import database_url
            self.db_url = database_url

    def register_tweet(self, tweet, reply):
        '''
        Registers a tweet as having been replied to in the database
        '''
        with dataset.connect(self.db_url) as db:
            table = db['tweets']
            gif_url = reply.entities['urls'][0]["expanded_url"]
            table.insert(dict(tweet_id=tweet.id, reply_id=reply.id,\
             gif_url=gif_url))

    def check_for_existing_reply(self, tweet):
        '''
        Searches the database to see if the given tweet was already 
        replied to.
        :return: Boolean value. `True` if the given tweet has been 
        replied to previously 
        '''
        db = dataset.connect(self.db_url)
        existing_id = db['tweets'].find_one(tweet_id=tweet.id)
        if existing_id is not None:
            return True
        else:
            return False

    def mark_youtube_invalid(self, youtube_url):
        with dataset.connect(self.db_url) as db:
            table = db['youtubes']
            table.upsert(dict(youtube_url=youtube_url, invalid=True), 
                ['youtube_url', 'invalid'])

    def is_youtube_invalid(self, youtube_url):
        '''
        :return: True if youtube invalid, false if not invalid.
        '''
        db = dataset.connect(self.db_url)
        existing_youtube = db['youtubes'].find_one(youtube_url=youtube_url)
        if existing_youtube is not None and existing_youtube['invalid']:
            return True
        else:
            return False

    def filter_replied(self, tweets, database=None):
        '''
        Filters the given `tweets` array for tweets already replied to.

        Use this method instead of `check_for_existing_reply` to reduce
        database connect actions, cutting down on time.

        :tweets: An array of tweepy Status objects
        :database: A dataset connection to the database.
        If not provided, this method will create a database connection

        :return: An array of tweepy Status objects representing tweets
        that have not yet been replied to.
        '''
        new_tweets = []
        if database is None:
            database = dataset.connect(self.db_url)
        table = database.load_table('tweets')
        for tweet in tweets:
            existing_id = table.find_one(tweet_id=tweet.id)
            if existing_id is None:
                new_tweets.append(tweet)
        return new_tweets

    def filter_invalid_youtube(self, tweets, database=None):
        '''
        Filters the given `tweets` array for tweets with valid YouTube
        URLs. 

        "Invalid" YouTube URLs are URLs that have been tried in the past
        and resulted in some kind of error.

        :tweets: Array of tweepy Status objects
        :database: dataset connection to the database. If not provided,
        this method will create one for itself.

        :return: an array of tweepy Status objects that contain YouTube
        URLs that are yet to be determined as invalid.
        '''
        valid_tweets = []
        if database is None:
            database = dataset.connect(self.db_url)
        table = database.load_table('youtubes')
        parser = tweet_parser.TweetParser()
        for tweet in tweets:
            youtube_url = parser.find_youtube_url(tweet)
            existing_youtube = table.find_one(youtube_url=youtube_url)
            if existing_youtube is None:
                valid_tweets.append(tweet)
        return valid_tweets

    def find_hot_new_tweets(self, tweets):
        '''
        Filters the given array of tweets, removing tweets that have
        already been replied to or have YouTube links that have not 
        worked in the past.

        :tweets: Array of tweepy Status objects

        :return: Array of tweepy Status objects
        '''
        database = dataset.connect(self.db_url)
        return self.filter_invalid_youtube(
            self.filter_replied(tweets, database=database),
            database=database)
