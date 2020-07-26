import unittest
from mock import patch, MagicMock
from tests import helpers
from better_auto_moderator.moderators.moderator import Moderator, ModeratorAuthorChecks
from better_auto_moderator.rule import Rule
from better_auto_moderator.reddit import reddit
from datetime import datetime
from dateutil.relativedelta import relativedelta

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

    def test_multiple_values(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'id': ['abcde', 'fghij'],
            'action': 'remove'
        })
        assert mod.moderate(rule), "Matches fail with multiple values"

        rule = Rule({
            'id': ['fghij', 'abcde'],
            'action': 'remove'
        })
        assert mod.moderate(rule), "Matches fail with multiple values, when correct value is not first"

    def test_multiple_checks(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'id+body (full-exact)': 'abcde',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Matches fail when checks are combined"

        rule = Rule({
            'id+body (full-exact)': 'Hello, world!',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Matches fail when checks are combined"

        rule = Rule({
            'id+body (full-exact)': 'not there',
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
            'body (full-exact)': 'Hello, {{author}}',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Author placeholder is not replaced"

        comment.body = "Hello, %s, how are you %s?" % (comment.author.name, comment.author.name)

        rule = Rule({
            'body (full-exact)': 'Hello, {{author}}, how are you {{author}}?',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Author placeholder is not replaced when there are multiple matches"


    def test_author_flair_text(self):
        post = helpers.post()
        rule = Rule({
            'author': {
                'flair_text': 'test'
            },
            'action': 'remove'
        })
        mod = Moderator(post)

        flair_mock = MagicMock(return_value=iter([{ 'flair_text': 'test' }]))
        post.subreddit.flair = flair_mock

        assert mod.moderate(rule), "Author flair_text not matching"

        flair_mock.return_value = iter([{ 'flair_text': 'nomatch' }])
        self.assertFalse(mod.moderate(rule), "Author flair_text matching as a false positive")


    def test_author_flair_css_class(self):
        post = helpers.post()
        rule = Rule({
            'author': {
                'flair_css_class': 'test'
            },
            'action': 'remove'
        })
        mod = Moderator(post)

        flair_mock = MagicMock(return_value=iter([{ 'flair_css_class': 'test' }]))
        post.subreddit.flair = flair_mock

        assert mod.moderate(rule), "Author flair_css_class not matching"

        flair_mock.return_value = iter([{ 'flair_css_class': 'nomatch' }])
        self.assertFalse(mod.moderate(rule), "Author flair_css_class matching as a false positive")

    def test_author_flair_template_id(self):
        post = helpers.post()
        rule = Rule({
            'author': {
                'flair_template_id': 'test'
            },
            'action': 'remove'
        })
        mod = Moderator(post)

        flair_mock = MagicMock(return_value= { 'current': { 'flair_template_id': 'test' } })
        old_post = reddit.post
        reddit.post = flair_mock

        assert mod.moderate(rule), "Author flair_template_id not matching"

        flair_mock.return_value = { 'current': { 'flair_template_id': 'nomatch' } }
        self.assertFalse(mod.moderate(rule), "Author flair_template_id matching as a false positive")

        reddit.post = old_post

    def test_regex_match(self):
        comment = helpers.comment()
        comment.body = 'Hello, foo! How are you?'
        mod = Moderator(comment)

        rule = Rule({
            'body (full-exact, regex)': 'Hello, [A-za-z]+! How are you\\?',
            'action': 'remove'
        })
        assert mod.moderate(rule), "Regex match failing to match"

        comment.body = 'Hello, Foo Bar! How are you?'
        self.assertFalse(mod.moderate(rule), "Regex match matching as false positive")

    def test_starts_with(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'body (starts-with)': 'Hello',
            'action': 'remove'
        })
        assert mod.moderate(rule), "starts-with match failing to match"

        comment.body = 'Wassup, buddy?'
        self.assertFalse(mod.moderate(rule), "starts-with match matching as false positive")

    def test_full_text(self):
        comment = helpers.comment()
        comment.body = ' .# Hello, world! # ..'
        mod = Moderator(comment)

        rule = Rule({
            'body (full-text)': 'Hello, world',
            'action': 'remove'
        })
        assert mod.moderate(rule), "full-text match failing to match"

        comment.body = ' .# Hello, world'
        assert mod.moderate(rule), "full-text match failing with just leading symbols"

        comment.body = ' Hello, world! # ..'
        assert mod.moderate(rule), "full-text match failing with just following symbols"

        comment.body = ' .# Hello, world! # Cya! ..'
        self.assertFalse(mod.moderate(rule), "full-text match matching as false positive")

    def test_include(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'body (includes)': 'Ell',
            'action': 'remove'
        })
        assert mod.moderate(rule), "include match failing to match"

        rule = Rule({
            'body (includes)': 'lo, ',
            'action': 'remove'
        })
        assert mod.moderate(rule), "include match failing to match with word boundaries"

        comment.body = "Hello world"
        self.assertFalse(mod.moderate(rule), "include match matching as a false positive")

    def test_includes_regex(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'body (includes, regex)': 'Hello!?',
            'action': 'remove'
        })
        assert mod.moderate(rule), "include match with regex failing to match"


    def test_full_exact_regex(self):
        comment = helpers.comment()
        mod = Moderator(comment)

        rule = Rule({
            'body (full-exact, regex)': 'Hello,? world!?',
            'action': 'remove'
        })
        assert mod.moderate(rule), "full_exact match with regex failing to match"

    def test_reports(self):
        rule = Rule({
            'reports': 2,
            'action': 'approve'
        })

        comment = helpers.comment()
        comment.user_reports = [
            ['abcde', 1],
            ['edcba', 1]
        ]
        comment.mod_reports = []
        mod = Moderator(comment)
        assert mod.moderate(rule), "Reports (count) not passing when the list contains same number of values"

        comment = helpers.comment()
        comment.user_reports = [['fghij', 1]]
        comment.mod_reports = [['edcba', 1]]
        mod = Moderator(comment)
        assert mod.moderate(rule), "Reports (count) are not passing when the list contains the appropriate value between user and mod reports"

        comment.mod_reports = []
        mod = Moderator(comment)
        self.assertFalse(mod.moderate(rule), "Reports (count) matching as false positive")

    def test_body_longer_than(self):
        comment = helpers.comment()
        comment.body = "Hello, world"
        rule = Rule({
            'body_longer_than': len(comment.body) - 1, # Removing 2 because the "!" will be removed
            'action': 'approve'
        })

        mod = Moderator(comment)
        assert mod.moderate(rule), "body_longer_than not matching"

        comment.body = comment.body[:-1]
        self.assertFalse(mod.moderate(rule), 'body_longer_than matching when lengths are equal')

        comment.body = comment.body[:-1]
        self.assertFalse(mod.moderate(rule), 'body_longer_than matching when the body is too short')

    def test_body_shorter_than(self):
        comment = helpers.comment()
        rule = Rule({
            'body_shorter_than': len(comment.body) + 1,
            'action': 'approve'
        })

        mod = Moderator(comment)
        assert mod.moderate(rule), "body_shorter_than not matching"

        comment.body = comment.body + 'a'
        self.assertFalse(mod.moderate(rule), 'body_shorter_than matching when lengths are equal')

        comment.body = comment.body + 'a'
        self.assertFalse(mod.moderate(rule), 'body_shorter_than matching when the body is too long')

    def test_is_edited(self):
        comment = helpers.comment()
        rule = Rule({
            'is_edited': True,
            'action': 'approve'
        })

        comment.edited = True
        mod = Moderator(comment)
        assert mod.moderate(rule), "is_edited not matching"

        comment.edited = False
        self.assertFalse(mod.moderate(rule), "is_edited matching as false positive")

    def test_crosspost_name_check(self):
        old_submission = reddit.submission
        og_post = helpers.post()
        reddit.submission = MagicMock(return_value=og_post)

        post = helpers.post()
        rule = Rule({
            'crosspost_subreddit': {
                'name': 'Cross'
            },
            'action': 'approve'
        })

        mod = Moderator(post)
        og_post.subreddit.name = "Cross Sub"
        self.assertFalse(mod.moderate(rule), "crosspost_subreddit name matching even when post is not a crosspost")

        post.crosspost_parent = 't3_abcde'
        assert mod.moderate(rule), "crosspost_subreddit name not matching"

        og_post.subreddit.name = "TestSub"
        self.assertFalse(mod.moderate(rule), "crosspost_subreddit name matching as false positive")

        reddit.submission = old_submission

    def test_crosspost_is_nsfw_check(self):
        old_submission = reddit.submission
        og_post = helpers.post()
        reddit.submission = MagicMock(return_value=og_post)

        post = helpers.post()
        rule = Rule({
            'crosspost_subreddit': {
                'is_nsfw': True
            },
            'action': 'approve'
        })

        mod = Moderator(post)
        og_post.subreddit.over18 = True
        self.assertFalse(mod.moderate(rule), "crosspost_subreddit is_nsfw matching even when post is not a crosspost")

        post.crosspost_parent = 't3_abcde'
        assert mod.moderate(rule), "crosspost_subreddit is_nsfw not matching"

        og_post.subreddit.over18 = False
        self.assertFalse(mod.moderate(rule), "crosspost_subreddit is_nsfw matching as false positive")

        reddit.submission = old_submission

    def test_account_age(self):
        post = helpers.post()
        mod = Moderator(post)

        rule = Rule({
            'author': {
                'account_age': '> 10 minutes'
            },
            'action': 'approve'
        })
        post.author.created_utc = (datetime.today() + relativedelta(minutes=-11)).timestamp()
        assert mod.moderate(rule), "account_age not matching for minutes"
        post.author.created_utc = (datetime.today() + relativedelta(minutes=-9)).timestamp()
        self.assertFalse(mod.moderate(rule), "account_age matching as false positive for minutes")

        rule = Rule({
            'author': {
                'account_age': '> 10 hours'
            },
            'action': 'approve'
        })
        post.author.created_utc = (datetime.today() + relativedelta(hours=-11)).timestamp()
        assert mod.moderate(rule), "account_age not matching for hours"
        post.author.created_utc = (datetime.today() + relativedelta(hours=-9)).timestamp()
        self.assertFalse(mod.moderate(rule), "account_age matching as false positive for hours")

        rule = Rule({
            'author': {
                'account_age': '> 10 days'
            },
            'action': 'approve'
        })
        post.author.created_utc = (datetime.today() + relativedelta(days=-11)).timestamp()
        assert mod.moderate(rule), "account_age not matching for days"
        post.author.created_utc = (datetime.today() + relativedelta(days=-9)).timestamp()
        self.assertFalse(mod.moderate(rule), "account_age matching as false positive for days")

        rule = Rule({
            'author': {
                'account_age': '> 10 weeks'
            },
            'action': 'approve'
        })
        post.author.created_utc = (datetime.today() + relativedelta(weeks=-11)).timestamp()
        assert mod.moderate(rule), "account_age not matching for weeks"
        post.author.created_utc = (datetime.today() + relativedelta(weeks=-9)).timestamp()
        self.assertFalse(mod.moderate(rule), "account_age matching as false positive for weeks")

        rule = Rule({
            'author': {
                'account_age': '> 10 years'
            },
            'action': 'approve'
        })
        post.author.created_utc = (datetime.today() + relativedelta(years=-11)).timestamp()
        assert mod.moderate(rule), "account_age not matching for years"
        post.author.created_utc = (datetime.today() + relativedelta(years=-9)).timestamp()
        self.assertFalse(mod.moderate(rule), "account_age matching as false positive for years")

    def test_spam(self):
        post = helpers.post()
        rule = Rule({
            'id': post.id,
            'action': 'spam'
        })
        mod = Moderator(post)

        post.mod.remove.reset_mock()
        mod.moderate(rule)
        post.mod.remove.assert_called_with(spam=True)

    def test_report(self):
        post = helpers.post()
        rule = Rule({
            'id': post.id,
            'action': 'report'
        })
        mod = Moderator(post)

        post.report.reset_mock()
        mod.moderate(rule)
        post.report.assert_called_with(None)

        rule = Rule({
            'id': post.id,
            'action': 'report',
            'action_reason': 'Just cuz'
        })
        post.report.reset_mock()
        mod.moderate(rule)
        post.report.assert_called_with('Just cuz')

    def test_set_author_flair(self):
        post = helpers.post()
        mod = Moderator(post)
        flair_mock = MagicMock()
        post.subreddit.flair.set = flair_mock
        old_get_flair = ModeratorAuthorChecks.flair_text.__wrapped__
        get_flair_mock = MagicMock(return_value=None)
        ModeratorAuthorChecks.flair_text.__wrapped__ = get_flair_mock

        # Sets text
        mod.moderate(Rule({
            'id': post.id,
            'author': {
                'set_flair': 'test'
            }
        }))
        flair_mock.assert_called_with(text='test')

        # Sets both text and css
        flair_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'author': {
                'set_flair': ['test', 'csstest']
            }
        }))
        flair_mock.assert_called_with(text='test', css_class='csstest')

        # Raises an exception if a dictionary is passed with no template_id
        with self.assertRaises(Exception):
            mod.moderate(Rule({
                'id': post.id,
                'author': {
                    'set_flair': {
                        'text': 'test'
                    }
                }
            }))

        # Sets template_id, text, and css
        flair_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'author': {
                'set_flair': {
                    'template_id': 'idtest',
                    'text': 'test',
                    'css_class': 'csstest'
                }
            }
        }))
        flair_mock.assert_called_with(text='test', css_class='csstest', template_id='idtest')

        # Does not set new flair, because overwrite_flair is not set
        flair_mock.reset_mock()
        get_flair_mock.return_value = 'before'
        mod.moderate(Rule({
            'id': post.id,
            'author': {
                'set_flair': 'test'
            }
        }))
        flair_mock.assert_not_called()

        mod.moderate(Rule({
            'id': post.id,
            'author': {
                'set_flair': 'test',
                'overwrite_flair': True
            }
        }))
        flair_mock.assert_called_with(text='test')

        ModeratorAuthorChecks.flair_text.__wrapped__ = old_get_flair

    def test_set_sticky(self):
        post = helpers.post()
        mod = Moderator(post)
        sticky_mock = MagicMock()
        post.mod.distinguish = sticky_mock

        # Sets text
        mod.moderate(Rule({
            'id': post.id,
            'set_sticky': True
        }))
        sticky_mock.assert_called_with('yes', sticky=True)

        sticky_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'set_sticky': 1
        }))
        sticky_mock.assert_called_with('yes', sticky=True)

        sticky_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'set_sticky': False
        }))
        sticky_mock.assert_called_with('no', sticky=False)

    def test_set_locked(self):
        post = helpers.post()
        mod = Moderator(post)
        lock_mock = MagicMock()
        unlock_mock = MagicMock()
        post.mod.lock = lock_mock
        post.mod.unlock = unlock_mock

        mod.moderate(Rule({
            'id': post.id,
            'set_locked': True
        }))
        lock_mock.assert_called()
        unlock_mock.assert_not_called()

        lock_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'set_locked': False
        }))
        lock_mock.assert_not_called()
        unlock_mock.assert_called()

    def test_ignore_blockquotes(self):
        rule = Rule({
            'ignore_blockquotes': True
        })
        comment = helpers.comment()
        mod = Moderator(comment)

        # test
        #     test <-- removed
        #          <-- removed
        #     test <-- removed
        # test
        comment.body = "test\n    test\n    \n    test\ntest"
        self.assertEqual(len(mod.checks.body.__wrapped__(mod, rule, [])), 9)

        comment.body = "test ```test\ntest\n    test\n  test\ntest``` test"
        self.assertEqual(len(mod.checks.body.__wrapped__(mod, rule, [])), 10)

    def test_match(self):
        comment = helpers.comment()
        comment.body = "comment with id %s" % comment.id
        rule = Rule({
            'id': comment.id,
            'body (full-exact)': 'comment with id {{match-id}}',
            'action': 'approve'
        })
        mod = Moderator(comment)

        assert mod.moderate(rule), 'Match not injecting itself'

        comment.id = 'fghij'
        self.assertFalse(mod.moderate(rule), 'Match injecting incorrectly')
