import praw
from unittest.mock import patch, PropertyMock, MagicMock

def comment():
    comment = praw.models.Comment({}, None, None, {
        'id': 'abcde',
        'body': 'Hello, world!',
        'author': redditor()
    })
    sub = PropertyMock(return_value=subreddit())
    type(comment).subreddit = sub
    comment.mod.approve = MagicMock(return_value=True)
    comment.mod.remove = MagicMock(return_value=True)

    return comment

def redditor():
    return praw.models.Redditor({}, None, None, {
        'name': 'test_user'
    })

def subreddit():
    return praw.models.Subreddit({}, 'BAMTest')
