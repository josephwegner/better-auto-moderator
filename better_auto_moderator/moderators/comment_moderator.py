from better_auto_moderator.moderators.moderator import Moderator

"""
    'comment_locked'
    'comment_stickied',
    'is_top_level'
"""

class CommentModerator(Moderator):
    def __init__(self, item):
        super().__init__(item)
