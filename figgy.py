# Fetch video, create gif, upload to gfycat, post to twitter

import yubtub
import gfycat
import tweepy
import time
import logging
import sys
import os, errno

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
from keys import keys
auth = tweepy.OAuthHandler(keys['consumer_token'], keys['consumer_secret'])
auth.set_access_token(keys['access_key'], keys['access_secret'])
api = tweepy.API(auth)


def upload_gif(youtube_url):
    '''
    Creates a gif of a randomly selected section of the given video

    :youtube_url: URL of the youtube video to create a gif from
    :return: URL to the gfycat page for the gif
    '''
    try:
        logging.debug("Downloading video from %s" % youtube_url)
        gif_filename = yubtub.generate_gif(youtube_url)
    except Exception, e:
        logging.exception(e)
    else:   
        logging.debug("Downloaded video from youtube")
        try:
            gfy_result = gfycat.gfycat().uploadFile(gif_filename)
        except Exception, e:
            logging.excpetion(e)
        else:
            gfy_url = "http://gfycat.com/" + gfy_result.get("gfyName")
            logging.info("Uploaded gif: %s" % gfy_result)
            return gfy_url

def tweet_gif(youtube_url):
    '''
    Tweets a randomly created gif from a youtube video.

    :youtube_url: URL of the youtube video to gif
    '''
    try:
        logging.debug("Uploading gif from youtube: %s" % youtube_url)
        url = upload_gif(youtube_url);
    except Exception, e:
        logging.excpetion(e)
    else:
        logging.info("Gif created, posting to twitter")
        api.update_status(url)
        logging.debug("Posted URL for youtube video %s" % youtube_url)
    

if __name__ == "__main__":
    print "Testing tweeting gif"
    # tweet_gif("https://www.youtube.com/watch?v=cV9p5SG-5-o")
    tweet_gif("https://www.youtube.com/watch?v=N2bCc0EGP6U")
