import logging
import re

def find_youtube_url(tweet):
    '''
    Finds and returns a youtube URL from the given tweet, if it contains
    one.

    :tweet: Tweepy `Status` object, representing a tweet
    '''
    for entityDict in tweet.entities['urls']:
        candidate = entityDict['expanded_url']

        # determine if url is youtube url
        youtube_re = re.compile("http[s]?://(www.)?youtube.com/watch\?v=.{,11}")
        match = youtube_re.match(candidate)
        if match is not None:
            return match.group()

    # If reaching here, looped through all URLs and none of them are yubtub :(
    return None

def find_mentions_with_youtubes(api):
    '''
    Searches through the recent mentions for a user, finding mentions
    that have a youtube URL. Returns a list of tuples, of form:
        (mention, youtube_url)

    :api: the authenticated Tweepy API object that will perform the net
    call for mentions

    :return: A list of tupes of form: (mention, youtube_url)
    '''
    try:
        mentions = api.mentions_timeline()
    except Exception, e:
        logging.exception(e)
        raise e
    else:
        if len(mentions) > 0:
            yubtub_mentions = []
            for mention in mentions:
                yubtub = find_youtube_url(mention)
                if yubtub is not None:
                    logging.debug("Found youtube link (%s) in tweet (%s)"\
                     % (yubtub, mention.text))
                    yubtub_mentions.append((mention,yubtub))
            return yubtub_mentions
        else:
            # No mentions :(
            logging.debug("No mentions found")
            return []
