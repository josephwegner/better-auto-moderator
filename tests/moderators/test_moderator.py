import unittest
from mock import patch, MagicMock
from tests import helpers
from better_auto_moderator.moderators.moderator import Moderator
from better_auto_moderator.rule import Rule
from better_auto_moderator.reddit import reddit

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

        flair_mock = MagicMock(return_value={ 'flair_text': 'test' })
        post.subreddit.flair = flair_mock

        assert mod.moderate(rule), "Author flair_text not matching"

        flair_mock.return_value = { 'flair_text': 'nomatch' }
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

        flair_mock = MagicMock(return_value={ 'flair_css_class': 'test' })
        post.subreddit.flair = flair_mock

        assert mod.moderate(rule), "Author flair_css_class not matching"

        flair_mock.return_value = { 'flair_css_class': 'nomatch' }
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
