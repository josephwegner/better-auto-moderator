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

    def test_multiple_checks(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'id+body': 'abcde',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Matches fail when checks are combined"

        rule = Rule({
            'id+body': 'Hello, world!',
            'action': 'remove'
        })
        print('start')
        assert mod.moderate(rule), "Matches fail when checks are combined"

        rule = Rule({
            'id+body': 'not there',
            'action': 'remove'
        })
        self.assertFalse(mod.moderate(rule), "Matches when checks are combined")

    def test_negation(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'id': 'abcde',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Doesn't match when validity is default"


        rule = Rule({
            '~id': 'abcde',
            'action': 'remove'
        })
        self.assertFalse(mod.moderate(rule), "Matches when validity is default")

        rule = Rule({
            'id': 'test',
            'action': 'remove'
        })
        self.assertFalse(mod.moderate(rule), "Matches when validity is default and there's no actual match")


        rule = Rule({
            '~id': 'test',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Doesn't match when validity is default, but there's no actual match"

    def test_lowercase_checks(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'id (full-text)': 'AbCdE',
            'action': 'remove'
        })
        assert mod.moderate(rule), "full-text doesn't match when some letters are uppercase"

        rule = Rule({
            'id (full-text, case-sensitive)': 'AbCdE',
            'action': 'remove'
        })
        self.assertFalse(mod.moderate(rule), "full-text matches even when some letters are uppercase and case-sensitive is on")

    def test_author_checks(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'author': {
                'post_karma': '> 5'
            },
            'action': 'remove'
        })
        assert mod.moderate(rule), "basic author checks are failing"

        rule = Rule({
            'author': {
                'post_karma': '> 15'
            },
            'action': 'remove'
        })
        self.assertFalse(mod.moderate(rule), "basic author checks are throwing false positive")

    def test_placeholders(self):
        comment = helpers.comment()
        comment.body = "Hello, %s" % comment.author.name
        mod = Moderator(comment)

        rule = Rule({
            'body': 'Hello, {{author}}',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Author placeholder is not replaced"
