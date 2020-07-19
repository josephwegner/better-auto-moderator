import praw
from os import environ

reddit = praw.Reddit(client_id=environ.get('REDDIT_CLIENT_ID'),
                     client_secret=environ.get('REDDIT_CLIENT_SECRET'),
                     user_agent="ATS Dev",
                     username=environ.get('REDDIT_USERNAME'),
                     password=environ.get('REDDIT_PASSWORD'))
subreddit = reddit.subreddit(environ.get('REDDIT_SUBREDDIT'))

def update_automod_config(new_yaml):
    print("Updating automod config...")
    subreddit.wiki["config/automoderator"].edit(new_yaml, "BetterAutoModerator push")
