import unittest
from mock import patch, MagicMock
from tests import helpers
from better_auto_moderator.moderators.moderator import Moderator
from better_auto_moderator.rule import Rule

class ModeratorTestCase(unittest.TestCase):

    def test_moderators_exempt_default(self):
        comment = helpers.comment()
        mod = Moderator(comment)
        rule = Rule({
            'id': 'abcde',
            'action': 'remove'
        })

        # Default, non-mod
        comment.author.moderated = MagicMock(return_value=[])
        assert mod.moderate(rule), "Default moderators_exempt is exempting normal redditors"

        # Default, mod
        comment.author.moderated = MagicMock(return_value=[comment.subreddit])
        self.assertFalse(mod.moderate(rule), "Default moderators_exempt is not exempting mods")

    def test_moderators_exempt_set(self):
        comment = helpers.comment()
        comment.author.moderated = MagicMock(return_value=[comment.subreddit])
        mod = Moderator(comment)

        # exempt True, mod
        rule = Rule({
            'id': 'abcde',
            'moderators_exempt': True,
            'action': 'remove'
        })
        self.assertFalse(mod.moderate(rule), "Moderators are not exempted when moderators_exempt is true")

        # exempt False, mod
        rule = Rule({
            'id': 'abcde',
            'moderators_exempt': False,
            'action': 'remove'
        })
        assert mod.moderate(rule), "Moderators are exempted even when moderators_exempt is false"
