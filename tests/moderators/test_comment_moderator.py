import unittest
from tests import helpers
from better_auto_moderator.moderators.comment_moderator import CommentModerator
from better_auto_moderator.rule import Rule

class CommentModeratorTestCase(unittest.TestCase):
    def test_is_top_level(self):
        rule = Rule({
            'is_top_level': True,
            'action': 'approve'
        })

        comment = helpers.comment()
        comment.depth = 0
        mod = CommentModerator(comment)
        assert mod.moderate(rule), "is_top_level not matching correctly"

        comment.depth = 1
        self.assertFalse(mod.moderate(rule), "is_top_level matching as a false positive")

    def test_is_submitter(self):
        rule = Rule({
            'author': {
                'is_submitter': True
            },
            'action': 'approve'
        })

        comment = helpers.comment()
        comment.author.id = 'abcde'
        comment.submission.author.id = 'abcde'
        mod = CommentModerator(comment)
        assert mod.moderate(rule), "is_submitted not matching correctly"

        comment.author.id = 'fghij'
        self.assertFalse(mod.moderate(rule), "is_submitter matching on a false positive")
