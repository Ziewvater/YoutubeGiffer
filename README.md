Randomized YouTube GIF Twitter Bot
===
The YouTubeGiffer bot controls a Twitter account that tweets GIFs that are created randomly created from a given YouTube video. The bot accepts tweets containing YouTube video URLs directed to the account as input, creates a GIF of random length and start time, and posts the GIF as a reply to the user who initially tweeted at the bot's account.

Currently, the bot does not post the GIF directly to Twitter, but rather uploads the image to Gfycat, and tweets the Gfycat URL for the GIF. This is done to circumvent the 3MB size cap on images on Twitter. Many of the images created through this bot are rather large, and would definitely not fit on Twitter.

Configuration
-------------
The YouTubeGiffer bot's authentication can be configured in two different ways: by setting up a key file named `keys.py`, or if being deployed on a Heroku server, using Heroku configuration variables.

### Heroku Configuration Variables 
If using Heroku's config variables to authenticate the bot, the following variables must be set:
* ACCESS_KEY: *Twitter account access key (API key)*
* ACCESS_SECRET: *Twitter account secret token (API secret)*
* CONSUMER_TOKEN: *Twitter app consumer token (API key)*
* CONSUMER_SECRET: *Twitter app secret token (API secret)*
* DATABASE_URL: *URL to a SQL database*

### Keys File
This bot script requires a configuration file named `keys.py`. Contained within the `keys.py` file, the authentication information for the Twitter app and Twitter account to be used are to be stored in a dictionary named `keys` of the following format:
```
keys = {
    consumer_token = "TOKEN", # Twitter app API key
    consumer_secret = "SECRET", # Twitter app API secret
    access_key = "ACCESS_KEY", # Twitter account API key
    access_secret = "ACCESS_SECRET", # Twitter account API secret
}
```

**Note:** As of now, the `keys.py` file approach has yet to be updated to accept a database URL.

<!--
Database Creation
-----------------
```
import dataset, sqlalchemy
db = dataset.connect(DATABASE_URL)
db.create_table('tweets')
db['tweets'].create_column('tweet_id', sqlalchempy.types.BigInteger)
db['tweets'].create_column('reply_id', sqlalchemy.types.BigInteger)
db['tweets'].create_column('gif_url', sqlalchemy.types.String)
```

Notes
-----
Need to remember to include OpenCV in the install script
-->
