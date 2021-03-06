# Fetch video, create gif, upload to gfycat, post to twitter

import yubtub
from yubtub import VideoAccessForbiddenException
import gfycat
import tweepy
import tweet_parser
import time
import logging
import sys
import os, errno
import database


####################
# Making Directories
####################

# Make logs directory
try:
    os.mkdir('Logs')
except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir('Logs'):
        pass
# Make videos directory
try:
    os.mkdir('Videos')
except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir('Videos'):
        pass
# Make gifs directory
try:
    os.mkdir('gifs')
except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir('gifs'):
        pass

####################
# Configuring Logger
####################

# Create new log file for run
current_date = time.strftime('%c')
log_file = 'Logs/Youtube.Jiffer'+current_date+".log"
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s: %(levelname)-8s %(message)s')

# Set logging level to DEBUG
logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)

# # Create stream handler to send INFO messages to console
# ch = logging.StreamHandler(sys.stdout)
# ch.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
# ch.setLevel(logging.INFO)
# # Add console handler to root logger
# logger.addHandler(ch)

#####################
# Configuring Twitter
#####################
# Grab authentication stuff from env
consumer_token = os.environ.get("CONSUMER_TOKEN")
consumer_secret = os.environ.get("CONSUMER_SECRET")
access_key = os.environ.get("ACCESS_KEY")
access_secret = os.environ.get("ACCESS_SECRET")

if consumer_token is None or consumer_secret is None\
 or access_key is None or access_secret is None:
    # If the environment doesn't have that info, grab it from the keys file
    from keys import keys
    if keys is not None:
        consumer_token = keys["consumer_token"]
        consumer_secret = keys["consumer_secret"]
        access_key = keys["access_key"]
        access_secret = keys["access_secret"]

    # If the keys file doesn't have all that info, throw exception
    if consumer_token is None or consumer_secret is None\
     or access_key is None or access_secret is None:
        raise Exception("No authentication information found")

auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)


######################
### CLI Attributes ###
######################
# If DRY_RUN is True, prevents Figgy from posting to Twitter, writing to DB
DRY_RUN = False

class Figgy(object):
    '''
    Figgy creates gifs with random lengths from YouTube videos. Videos
    are sourced from a connected Twitter account; they are collected
    through tweets directed at the account that contain a YouTube URL.
    '''

    def __init__(self):
        self.twitter_api_setup()

    def twitter_api_setup(self):
        consumer_token = os.environ.get("CONSUMER_TOKEN")
        consumer_secret = os.environ.get("CONSUMER_SECRET")
        access_key = os.environ.get("ACCESS_KEY")
        access_secret = os.environ.get("ACCESS_SECRET")

        if consumer_token is None or consumer_secret is None\
         or access_key is None or access_secret is None:
            # If the environment doesn't have that info, grab it from the keys file
            from keys import keys
            if keys is not None:
                consumer_token = keys["consumer_token"]
                consumer_secret = keys["consumer_secret"]
                access_key = keys["access_key"]
                access_secret = keys["access_secret"]

            # If the keys file doesn't have all that info, throw exception
            if consumer_token is None or consumer_secret is None\
             or access_key is None or access_secret is None:
                raise Exception("No authentication information found")

        auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
        auth.set_access_token(access_key, access_secret)
        self.api = tweepy.API(auth)

    def upload_gif(self, youtube_url):
        '''
        Creates a gif of a randomly selected section of the given video

        :youtube_url: URL of the youtube video to create a gif from
        :return: URL to the gfycat page for the gif
        '''
        try:
            yubtub = yubtub.YubTub(youtube_url)
            gif_filename = yubtub.generate_gif()
        except Exception as e:
            logging.exception(e)
            raise e
        else:   
            return self.gfycat_upload(gif_filename)

    def gfycat_upload(self, gif_filename):
        '''
        Uploads the GIF at the given filename to gfycat

        :return: URL to the gfycat page for the gif
        '''
        try:
            logging.debug("Uploading gif to gfycat")
            gfy_result = gfycat.gfycat().uploadFile(gif_filename)
        except Exception as e:
            logging.error("Could not upload gif to gfycat")
            logging.exception(e)
        else:
            gfy_url = "http://gfycat.com/" + gfy_result.get("gfyName")
            logging.info("Uploaded gif: %s" % gfy_result)
            return gfy_url

    def tweet_gif(self, youtube_url, tweet=None):
        '''
        Tweets a randomly created gif from a youtube video.

        :youtube_url: URL of the youtube video to gif
        :tweet: The tweet that the gif is in response to

        :return: The tweet generated with the gif
        '''
        logging.debug("Uploading gif from youtube: %s" % youtube_url)
        url = self.upload_gif(youtube_url);
        logging.info("Gif created, posting to twitter")

        post_tweets = True
        if hasattr(self, "dry_run"):
            post_tweets = not getattr(self, "dry_run")
        try:
            if tweet is not None:
                # Respond to given tweet
                tweet_text = "@%s %s" % (tweet.user.screen_name, str(url))
                if post_tweets:
                    tweet = self.api.update_status(
                        status=tweet_text,
                        in_reply_to_status_id=tweet.id
                        )
            else:
                # Just post the thing
                if post_tweets:
                    tweet = self.api.update_status(status=str(url))
            # Return the tweet for logging, etc.
            return tweet
        except Exception as e:
            logging.error("Error updating twitter status")
            logging.exception(e)
        else:
            logging.debug("Posted URL for youtube video %s" % youtube_url)
            logging.debug(tweet)

    def respond_to_mentions(self):
        '''
        Searches through mentions, finds mentions with youtube links, 
        responds to those tweets with a random gif from the youtube video.
        '''
        parser = tweet_parser.TweetParser()
        mentions = parser.find_mentions_with_youtubes(api)
        if len(mentions) > 0:
            # We are in business!
            logging.info("Found %i youtube tweets" % len(mentions))

            # Check against database to find the hot fresh content
            db = database.Database()
            only_tweets = [i[0] for i in mentions]

            hot_new_tweets = db.find_hot_new_tweets(only_tweets)

            logging.info("%i new tweets" % len(hot_new_tweets))
            for (tweet, youtube_url) in hot_new_tweets:
                logging.debug("New mention: <%s, %i>" % (tweet.text, tweet.id))
                try:
                    new_tweet = self.tweet_gif(youtube_url, tweet)
                except VideoAccessForbiddenException as e:
                    logging.error("Download failed, Forbidden")
                    db.mark_youtube_invalid(youtube_url)
                except Exception as e:
                    logging.error("Failed to respond to tweet! (<%s, %i>)" \
                        % (tweet.text, tweet.id))
                    logging.exception(e)
                    logging.debug("continuing with responding to tweets")
                else:
                    logging.info("Responded to tweet: <%s, %i> with new \
                        tweet <%s, %i>" % (tweet.text, tweet.id,\
                         new_tweet.text, new_tweet.id))
                    # Register tweet in database
                    logging.debug("Registering tweet: <%s, %i>" \
                        % (tweet.text, tweet.id))
                    db.register_tweet(tweet, new_tweet)
        else:
            # No tweets :(
            logging.info("No youtube mentions found")

if __name__ == "__main__":
    # When run from the CLI, this module will search for new mentions
    # and respond to them with gifs
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", help="performs tasks but without posting to twitter", action="store_true")
    parser.add_argument("-v", "--verbosity", help="Increase logging verbosity",
        action="store_true")
    parser.add_argument("-y", "--youtube", help="YouTube URL to fig")

    args = parser.parse_args()

    if args.verbosity:
        # Create stream handler to send INFO messages to console
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
        ch.setLevel(logging.DEBUG)
        # Add console handler to root logger
        logger.addHandler(ch)
    else:
        # Create stream handler to send INFO messages to console
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
        ch.setLevel(logging.INFO)
        # Add console handler to root logger
        logger.addHandler(ch)

    fig = Figgy()

    if args.dry_run:
        setattr(Figgy, "dry_run", True)

    if args.youtube:
        # If youtube is provided, just test youtube
        logging.info("Testing with given youtube %s" % args.youtube)
        fig.tweet_gif(args.youtube)
    else:
        logging.info("Starting process to search for and respond to mentions")
        fig.respond_to_mentions()
