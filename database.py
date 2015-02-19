# Database handler
import os
import dataset
import tweepy

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

        
