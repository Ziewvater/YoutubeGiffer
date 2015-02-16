# Fetch video, create gif, upload to gfycat, post to twitter

import yubtub
import gfycat
import tweepy
import tweet_parser
import time
import logging
import sys
import os, errno
import dataset
import urlparse

urlparse.uses_netloc.append("postgres")
env_url = os.environ.get("DATABASE_URL")
db_url = None
if env_url is not None:
    db_url = urlparse.urlparse(env_url)

if db_url is None:
    from keys import database_url
    print "Grabbing database url from keys"
    db_url = database_url

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

# Create stream handler to send INFO messages to console
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s'))
ch.setLevel(logging.INFO)
# Add console handler to root logger
logger.addHandler(ch)

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


def upload_gif(youtube_url):
    '''
    Creates a gif of a randomly selected section of the given video

    :youtube_url: URL of the youtube video to create a gif from
    :return: URL to the gfycat page for the gif
    '''
    try:
        gif_filename = yubtub.generate_gif(youtube_url)
    except Exception, e:
        logging.exception(e)
        raise e
    else:   
        try:
            logging.debug("Uploading gif to gfycat")
            gfy_result = gfycat.gfycat().uploadFile(gif_filename)
        except Exception, e:
            logging.error("Could not upload gif to gfycat")
            logging.excpetion(e)
        else:
            gfy_url = "http://gfycat.com/" + gfy_result.get("gfyName")
            logging.info("Uploaded gif: %s" % gfy_result)
            return gfy_url

def tweet_gif(youtube_url, tweet=None):
    '''
    Tweets a randomly created gif from a youtube video.

    :youtube_url: URL of the youtube video to gif

    :return: The tweet generated with the gif
    '''
    try:
        logging.debug("Uploading gif from youtube: %s" % youtube_url)
        url = upload_gif(youtube_url);
    except Exception, e:
        logging.excpetion(e)
    else:
        logging.info("Gif created, posting to twitter")
        try:
            if tweet is not None:
                # Respond to given tweet
                tweet_text = "@%s %s" % (tweet.user.screen_name, str(url))
                tweet = api.update_status(
                    status=tweet_text,
                    in_reply_to_status_id=tweet.id)
            else:
                # Just post the thing
                tweet = api.update_status(status=str(url))
            # Return the tweet for logging, etc.
            return tweet
        except Exception, e:
            logging.error("Error updating twitter status")
            logging.exception(e)
        else:
            logging.debug("Posted URL for youtube video %s" % youtube_url)
            logging.debug(tweet)

def respond_to_mentions():
    '''
    Searches through mentions, finds mentions with youtube links, 
    responds to those tweets with a random gif from the youtube video.
    '''
    mentions = tweet_parser.find_mentions_with_youtubes(api)
    if len(mentions) > 0:
        # We are in business!
        logging.info("Found %i youtube tweets" % len(mentions))
        for (tweet, youtube_url) in mentions:
            if not check_for_existing_reply(tweet):
                logging.debug("Found new mention: <%s, %i>" \
                    % (tweet.text, tweet.id))
                try:
                    new_tweet = tweet_gif(youtube_url, tweet)
                except Exception:
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
                    register_tweet(tweet, new_tweet)
            else:
                # Have already responded to this tweet, just let it go
                logging.debug("Already replied to tweet: <%s, %i>" \
                    % (tweet.text, tweet.id))
    else:
        # No tweets :(
        logging.info("No youtube mentions found")

def register_tweet(tweet, reply):
    '''
    Registers a tweet as having been replied to in the database
    '''
    with dataset.connect(db_url) as database:
        table = database['tweets']
        gif_url = reply.entities['urls'][0]
        table.insert(dict(tweet_id=tweet.id, reply_id=reply.id,\
         gif_url=gif_url))

def check_for_existing_reply(tweet):
    '''
    Searches the database to see if the given tweet was already replied
    to.
    :return: Boolean value. `True` if the given tweet has been replied
    to previously 
    '''
    database = dataset.connect(db_url)
    existing_id = database['tweets'].find_one(tweet_id=tweet.id)
    if existing_id is not None:
        return True
    else:
        return False

if __name__ == "__main__":
    # When run from the CLI, this module will search for new mentions
    # and respond to them with gifs
    logging.info("Starting process to search for and respond to mentions")
    respond_to_mentions()
