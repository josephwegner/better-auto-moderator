import unittest
from mock import MagicMock
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

    def test_parent_comment(self):
        comment = helpers.comment()
        parent_comment = helpers.comment()
        comment.parent = MagicMock(return_value=parent_comment)
        mod = CommentModerator(comment)

        rule = Rule({
            'parent_comment': {
                'id': 'test',
                'action': 'approve'
            }
        })
        comment.depth = 0
        self.assertFalse(mod.moderate(rule), "parent_comment matches even at depth=0")

        comment.depth = 1
        comment.id = 'test'
        self.assertFalse(mod.moderate(rule), "parent_comment matching on OG comment attributes")

        comment.id = 'abcde'
        parent_comment.id = 'test'
        parent_comment.mod.approve.reset_mock()
        assert mod.moderate(rule), "parent_comment not matching"
        parent_comment.mod.approve.assert_called()
