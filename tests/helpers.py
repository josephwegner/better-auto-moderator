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
    comment.user_reports = []
    comment.mod_reports = []
    comment.author.moderated = MagicMock(return_value=[])
    comment.mod.approve = MagicMock(return_value=True)
    comment.mod.remove = MagicMock(return_value=True)

    return comment

def redditor():
    user = praw.models.Redditor({}, None, None, {
        'name': 'test_user'
    })
    karma = PropertyMock(return_value=10)
    type(user).link_karma = karma
    type(user).comment_karma = karma

    return user

def post():
    post = praw.models.Submission({}, None, None, {
        'id': 'fghij',
        'title': 'A Post',
        'body': 'This is a post',
        'author': redditor(),
        'domain': "self.%s" % subreddit().name,
        'subreddit': subreddit().name,
        'media': None
    })
    sub = PropertyMock(return_value=subreddit())
    type(post).subreddit = sub
    post.author.moderated = MagicMock(return_value=[])
    post.mod.approve = MagicMock(return_value=True)
    post.mod.remove = MagicMock(return_value=True)

    return post

def subreddit():
    subreddit = praw.models.Subreddit({}, 'BAMTest')
    subreddit.name = 'BAMTest'
    return subreddit
