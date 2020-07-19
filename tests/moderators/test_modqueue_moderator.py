import unittest
from mock import patch, MagicMock
from tests import helpers
from better_auto_moderator.moderators.modqueue_moderator import ModqueueModerator
from better_auto_moderator.rule import Rule

class ModeratorTestCase(unittest.TestCase):

    def test_report_reasons_contains(self):
        rule = Rule({
            'report_reason': 'abcde',
            'action': 'approve'
        })

        comment = helpers.comment()
        comment.user_reports = [
            ['abcde', 1],
            ['edcba', 1]
        ]
        mod = ModqueueModerator(comment)
        assert mod.moderate(rule), "User reports not passing when the list contains the value"

        comment = helpers.comment()
        comment.user_reports = [
            ['fghij', 1],
            ['edcba', 1]
        ]
        mod = ModqueueModerator(comment)
        self.assertFalse(mod.moderate(rule), "User reports are passing when the list does not contain the value")

    def test_report_reasons_only(self):
        rule = Rule({
            'report_reason (only)': 'abcde',
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
        mod = ModqueueModerator(comment)
        self.assertFalse(mod.moderate(rule), "User reports (only) passing when a match exists alongside a non-match")

        comment = helpers.comment()
        comment.user_reports = [
            ['fghij', 1],
            ['edcba', 1]
        ]
        mod = ModqueueModerator(comment)
        self.assertFalse(mod.moderate(rule), "User reports (only) are passing when the list does not contain the value")
