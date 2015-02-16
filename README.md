Dumb Twitter Bot for Gifs by Z
===

Configuration
-------------
This bot script requires a configuration file named `keys.py`. Contained within the `keys.py` file, the authentication information for the Twitter app and Twitter account to be used are to be stored in a dictionary named `keys` of the following format:
```
keys = {
    consumer_token = "TOKEN",
    consumer_secret = "SECRET",
    access_key = "ACCESS_KEY",
    access_secret = "ACCESS_SECRET",
}
```

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
~~Need to remember to include OpenCV in the install script~~
Using a [buildpack](https://github.com/diogojc/heroku-buildpack-python-opencv-scipy) for OpenCV