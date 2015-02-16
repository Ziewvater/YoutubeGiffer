import pytube
from moviepy.editor import *
import random
import logging
import os

# Config
gif_folder_path = "gifs/"
videos_folder_path = "Videos/"
MAX_VIDEO_DIMENSION = 360.0
RESIZE_VIDEO = False#True

####################
# Methods and Such
####################
def grab_video(url):
    ''' 
    Downloads video from youtube url
    '''
    yt = pytube.YouTube()
    yt.url = url

    video_format = ""
    video = None
    if len(yt.videos) > 0:
        if yt.filter("mp4"):
            video_format = "mp4"
            video = yt.filter(video_format)[-1]
        try:
            new_vid_filename = videos_folder_path + video.filename + \
            "."+ video_format
            if os.path.exists(new_vid_filename):
                logging.debug("Video file already exists, using existing copy")
                return new_vid_filename
            else:
                video.download(videos_folder_path)
                logging.debug("Downloaded video \""+video.filename+"\"")
                return new_vid_filename
        except Exception as e:
            logging.error("Could not download video from URL: %s" % url)
            raise e
    else:
        # No vids!
        print "No videos found for %s" % url
        logging.error("No videos found for URL: %s" % url)
        raise Exception

def random_gif_from_video(video, length):
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


def generate_gif(url):
    '''
    :url: youtube video url

    :return: Filename for the new gif
    '''
    filename = ""
    try:
        filename = grab_video(url)
    except Exception as e:
        logging.error("Couldn't download video Youtube")
        logging.exception(e)
        raise e
    else:
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
        return random_gif_from_video(video, 2)


if __name__ == '__main__':
    print "Testing gif generation"
    generate_gif("https://www.youtube.com/watch?v=mtYMx9P0zgI") #ridged chips
    # generate_gif("https://www.youtube.com/watch?v=b3_lVSrPB6w") #horse
