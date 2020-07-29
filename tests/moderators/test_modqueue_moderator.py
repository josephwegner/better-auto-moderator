import unittest
from mock import patch, MagicMock
from tests import helpers
from better_auto_moderator.moderators.modqueue_moderator import ModqueueModerator
from better_auto_moderator.rule import Rule

class ModeratorTestCase(unittest.TestCase):

    def test_report_reasons_contains(self):
        rule = Rule({
            'report_reasons': 'abcde',
            'action': 'approve'
        })

        comment = helpers.comment()
        comment.user_reports = [
            ['abcde', 1],
            ['edcba', 1]
        ]
        comment.mod_reports = []
        mod = ModqueueModerator(comment)
        assert mod.moderate(rule), "User reports not passing when the list contains the value"

        comment = helpers.comment()
        comment.user_reports = [
            ['fghij', 1],
            ['edcba', 1]
        ]
        comment.mod_reports = []
        mod = ModqueueModerator(comment)
        self.assertFalse(mod.moderate(rule), "User reports are passing when the list does not contain the value")

    def test_report_reasons_only(self):
        rule = Rule({
            'report_reasons (only)': 'abcde',
            'action': 'approve'
        })

        comment = helpers.comment()
        comment.user_reports = [
            ['abcde', 1],
        ]
        mod = ModqueueModerator(comment)
        assert mod.moderate(rule), "User reports (only) not passing when only a match exists"

        comment = helpers.comment()
        comment.user_reports = [
            ['abcde', 1],
            ['edcba', 1]
        ]
        comment.mod_reports = []
        mod = ModqueueModerator(comment)
        self.assertFalse(mod.moderate(rule), "User reports (only) passing when a match exists alongside a non-match")

        comment = helpers.comment()
        comment.user_reports = [
            ['fghij', 1],
            ['edcba', 1]
        ]
        comment.mod_reports = []
        mod = ModqueueModerator(comment)
        self.assertFalse(mod.moderate(rule), "User reports (only) are passing when the list does not contain the value")

    def test_report_reasons_with_mod_reports(self):
        rule = Rule({
            'report_reasons': 'abcde',
            'action': 'approve'
        })

        comment = helpers.comment()
        comment.author.moderated = MagicMock(return_value=[comment.subreddit])
        comment.user_reports = [
            ['fghij', 1],
        ]
        comment.mod_reports = [
            ['abcde', 1]
        ]
        mod = ModqueueModerator(comment)
        assert mod.moderate(rule), "Report reasons don't match against mod reports"

        rule = Rule({
            'report_reasons': 'abcde',
            'action': 'approve',
            'moderators_exempt': True
        })
        self.assertFalse(mod.moderate(rule), "Report reasons include mod reports even when moderators_exempt is true")

    def test_contains_calls_full_text(self):
        rule = Rule({
            'report_reasons': 'abcde',
            'action': 'approve'
        })

        comment = helpers.comment()
        comment.user_reports = [
            ['fghij', 1],
        ]
        mod = ModqueueModerator(comment)
        old_full_exact = ModqueueModerator.full_exact
        ModqueueModerator.full_exact = MagicMock(return_value=True)
        mod.moderate(rule)

        mod.full_exact.assert_called()
        ModqueueModerator.full_exact = old_full_exact
