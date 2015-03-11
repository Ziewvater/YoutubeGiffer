import pytube
from pytube.exceptions import CipherError
from moviepy.editor import *
import random
import string
import logging
import os
from urllib2 import HTTPError

# Config
gif_folder_path = "gifs/"
videos_folder_path = "Videos/"
MAX_VIDEO_DIMENSION = 360.0
RESIZE_VIDEO = False#True

class VideoAccessForbiddenException(Exception):
    '''
    Unable to download video from YouTube
    '''
    pass

####################
# Methods and Such
####################
class YubTub(object):
    '''
    Downloads YouTube videos and creates gifs out of them
    '''

    def __init__(self, youtube_url):
        self.url = youtube_url

    def grab_video(self):
        ''' 
        Downloads video from youtube url

        :return: The path to the downloaded video file. If downloading the
        video was unsuccessful, will return `None`.
        '''
        yt = pytube.YouTube()
        try:
            yt.url = self.url
        except CipherError as e:
            logging.error("Cipher error, couldn't parse video")
            logging.exception(e)
            raise VideoAccessForbiddenException("Could not parse video")
        else:
            if len(yt.videos) > 0:
                video_format = ""
                video = None
                # TODO check for other filetypes for fallback
                if yt.filter("mp4"):
                    video_format = "mp4"
                    video = yt.filter(video_format)[-1] #-1 grabs biggest video
                    new_vid_filename = videos_folder_path + video.filename + \
                      "."+ video_format
                if os.path.exists(new_vid_filename):
                    # There's already a video file by that name, assume it's the same
                    logging.debug("Video file already exists, using existing copy")
                    return new_vid_filename
                try:
                    video.download(videos_folder_path)
                    logging.debug("Downloaded video \""+video.filename+"\"")
                    return new_vid_filename
                except HTTPError as http:
                    logging.error("Could not download video from URL: %s" % url)
                    logging.error("HTTP Error: "+str(http.code)+": "+str(http.reason))
                    raise VideoAccessForbiddenException("Could not download video: "
                      "(%i, %s)" % (http.code, http.reason))
                except CipherError as cipher:
                    logging.error("Cipher error, couln't parse video")
                    logging.exception(cipher)
                    raise VideoAccessForbiddenException("Could not parse video")
            else:
                # No vids!
                print "No videos found for %s" % url
                logging.error("No videos found for URL: %s" % url)
                return None

    def random_gif_from_video(self, video, length):
        '''
        Creates a gif from the given video object. The start time of the gif
        is randomly determined, and the gif runs for as long as the given
        length parameter.

        :video: VideoFileClip from moviepy
        :length: length of the gif to be made

        :return: The filename for the newly created gif
        '''
        if length > video.duration:
            logging.error("Desired length of the gif is longer than the video, aborting")
            return None

        # Determine the start and end times for the subclip
        start = random.random() * (video.duration - length)
        start_time = (0, start)
        end_time = (0, start+length)
        logging.debug("Creating gif from starting point %f" % start)

        newVid = video.subclip(start_time, end_time)
        newFilename = gif_folder_path + str(random.randint(0,100)) + "." + "gif"
        newVid.write_gif(newFilename)#, program="ImageMagick", fuzz=5)
        return newFilename


    def generate_gif(self):
        '''
        :url: youtube video url

        :return: Filename for the new gif
        '''
        filename = ""
        filename = self.grab_video()
        video = VideoFileClip(filename)
        if RESIZE_VIDEO:
            # Resize video if it's larger than the size limit in either dimension
            if video.size[0] > video.size[1]:
                # Resize first dimension
                if video.size[0] > MAX_VIDEO_DIMENSION:
                    logging.debug("Resizing by width. factor: %f" % (MAX_VIDEO_DIMENSION/video.size[0]))
                    video = video.resize(MAX_VIDEO_DIMENSION/video.size[0])
            else:
                # Resize second dimension:
                if video.size[1] > MAX_VIDEO_DIMENSION:
                    logging.debug("Resizing by height. Factor %f" % (MAX_VIDEO_DIMENSION/video.size[1]))
                    video = video.resize(MAX_VIDEO_DIMENSION/video.size[1])

        gif_duration = max((random.random() * video.duration),\
                        (1 if (video.duration > 1) else video.duration))
        logging.debug("Creating gif with duration %f" % gif_duration)
        return self.random_gif_from_video(video, 2)

    def create_gif(self, start_time, length, filename=None, destination=None):
        '''
        Creates a GIF with the YubTub's video with the given video start
        time and length.

        For this method to generate a GIF, the `url` parameter must be
        set to a valid YouTube url.

        :return: Filename for the new gif
        '''
        if not hasattr(self, "url"):
            logging.error("YubTub not initialized with URL")
            return None

        # Download the video
        video_filename = ""
        video_filename = self.grab_video()
        print "Video filename "+video_filename
        video = VideoFileClip(video_filename)

        if length > video.duration:
            logging.error("Desired length of the gif is longer than the video, aborting")
            return None
        if start_time + length > video.duration:
            logging.error("Desired length and starting time for the gif will "
                "run beyond end of video, aborting")
            return None

        # Determine the start and end times for the subclip
        start = (0, start_time)
        end = (0, start_time+length)
        logging.debug("Creating gif from starting point %f and length %f" % (start_time, length))
        print "Creating gif from starting point %f and length %f" % (start_time, length)

        if not filename:
            filename = self.generate_random_name()
            print "Generated name "+filename
        if destination is not None:
            filename = destination + filename
            print "Added destiation"
        # Add format
        filename += ".gif"
        print "Final filename: "+filename

        newVid = video.subclip(start, end)
        newVid.write_gif(filename)
        return filename

    def generate_random_name(self, length=8):
        return ''.join(random.choice(string.ascii_uppercase+string.ascii_lowercase) for _ in range(length))

if __name__ == '__main__':
    # print "Testing gif generation"
    # test_url = "https://www.youtube.com/watch?v=mtYMx9P0zgI" #ridged chips
    # yubber = YubTub(test_url)
    # yubber.create_gif(0, 4)
    # yubber.generate_gif() 
    # generate_gif("https://www.youtube.com/watch?v=b3_lVSrPB6w") #horse
    import argparse
    parser = argparse.ArgumentParser(description="Create GIFs from YouTube videos")
    parser.add_argument('youtube', help="URL of YouTube video to be used")
    parser.add_argument('start', help='Start timestamp within the video for the GIF', type=float)
    parser.add_argument('length', help='Desired length of the GIF', type=float)
    parser.add_argument('-f', '--filename', help='Name of the GIF to be created', type=str)
    parser.add_argument('-d', '--destination', help='Where to write the GIF. If not given, the GIF will be written in the current directory', type=str)

    args = parser.parse_args()
    if args.youtube:
        yubber = YubTub(args.youtube)
        yubber.create_gif(args.start, args.length, filename=args.filename, destination=args.destination)
