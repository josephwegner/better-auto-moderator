import unittest
from mock import patch, MagicMock, PropertyMock
from tests import helpers
from better_auto_moderator.moderators.post_moderator import PostModerator
from better_auto_moderator.rule import Rule
from better_auto_moderator.reddit import reddit

class ModeratorTestCase(unittest.TestCase):
    def test_title_check(self):
        rule = Rule({
            'title': 'Post',
            'action': 'approve'
        })

        post = helpers.post()
        mod = PostModerator(post)
        assert mod.moderate(rule), "Post titles not matching correctly"

        post.title = "Foobar"
        self.assertFalse(mod.moderate(rule), "Post titles matching as a false positive")

    def test_domain_textpost_check(self):
        post = helpers.post()
        rule = Rule({
            'domain': "self.%s" % post.subreddit.name,
            'action': 'approve'
        })

        mod = PostModerator(post)
        assert mod.moderate(rule), "Post domains not matching textposts correctly"

        post.domain = "foobar"
        self.assertFalse(mod.moderate(rule), "Post domains matching textposts as a false positive")

    def test_domain_linkpost_check(self):
        post = helpers.post()
        post.domain = "example.com"
        rule = Rule({
            'domain': "example.com",
            'action': 'approve'
        })

        mod = PostModerator(post)
        assert mod.moderate(rule), "Post domains not matching linkposts correctly"

        post.domain = "www.example.com"
        assert mod.moderate(rule), "Post domains not matching linkpost subdomains correctly"

        post.domain = "google.com"
        self.assertFalse(mod.moderate(rule), "Post domains not matching as a false positive")

        post.domain = "www.google.com"
        self.assertFalse(mod.moderate(rule), "Post domains for subdomains not matching as a false positive")

    def test_flair_text_check(self):
        rule = Rule({
            'flair_text': 'test',
            'action': 'approve'
        })

        post = helpers.post()
        post.link_flair_text = 'test'
        mod = PostModerator(post)
        assert mod.moderate(rule), "Post flair_text not matching correctly"

        post.link_flair_text = "Foobar"
        self.assertFalse(mod.moderate(rule), "Post flair_text matching as a false positive")

    def test_flair_css_class_check(self):
        rule = Rule({
            'flair_css_class': 'test',
            'action': 'approve'
        })

        post = helpers.post()
        post.link_flair_css_class = 'test'
        mod = PostModerator(post)
        assert mod.moderate(rule), "Post flair_css_class not matching correctly"

        post.link_flair_css_class = "foobar"
        self.assertFalse(mod.moderate(rule), "Post flair_css_class matching as a false positive")

    def test_flair_template_id_check(self):
        rule = Rule({
            'flair_template_id': 'test',
            'action': 'approve'
        })

        post = helpers.post()
        post.link_flair_template_id = 'test'
        mod = PostModerator(post)
        assert mod.moderate(rule), "Post flair_template_id not matching correctly"

        post.link_flair_template_id = "foobar"
        self.assertFalse(mod.moderate(rule), "Post flair_template_id matching as a false positive")

    def test_poll_option_text_check(self):
        rule = Rule({
            'poll_option_text (full-exact)': 'Is this a test?',
            'action': 'approve'
        })

        class PollData:
            def __init__(self):
                self.options = [
                    'Is this a test?',
                    'Or is this just fantasy?'
                ]

        poll_data = PollData()
        post = helpers.post()
        type(post).poll_data = PropertyMock(return_value=poll_data)

        mod = PostModerator(post)
        assert mod.moderate(rule), "Post poll_option_text not matching first option correctly"

        poll_data.options = ["Is this real life?", "Is this a test?"]
        assert mod.moderate(rule), "Post poll_option_text not matching first option correctly"

        poll_data.options = ["Is this real life?", "Or is this just fantasy?"]
        self.assertFalse(mod.moderate(rule), "Post poll_option_text matching as a false positive")

        type(post).poll_data = None

    def test_poll_option_count_check(self):
        rule = Rule({
            'poll_option_count': 2,
            'action': 'approve'
        })

        class PollData:
            def __init__(self):
                self.options = [
                    'test',
                    'test2'
                ]

        poll_data = PollData()
        post = helpers.post()
        type(post).poll_data = PropertyMock(return_value=poll_data)

        mod = PostModerator(post)
        assert mod.moderate(rule), "Post poll_option_count not matching correctly"

        poll_data.options = ["test", "test2", "test3"]
        self.assertFalse(mod.moderate(rule), "Post poll_option_count matching as a false positive")

        type(post).poll_data = None

    def test_crosspost_base_fields(self):
        old_submission = reddit.submission
        og_post = helpers.post()
        reddit.submission = MagicMock(return_value=og_post)
        og_post.selftext = "This is a crosspost"
        og_post.domain = "self.NotMySub"
        og_post.url = "www.notmypost.com"

        post = helpers.post()
        post.crosspost_parent = 't3_abcde'
        rule = Rule({})
        mod = PostModerator(post)

        self.assertEqual(mod.checks.body.__wrapped__(mod.checks, rule, []), "This is a crosspost", "Crosspost body not being retrieved")
        self.assertEqual(mod.checks.domain.__wrapped__(mod.checks, rule, []), "self.NotMySub", "Crosspost domain not being retrieved")
        self.assertEqual(mod.checks.url.__wrapped__(mod.checks, rule, []), "www.notmypost.com", "Crosspost url not being retrieved")

        reddit.submission = old_submission

    def test_crosspost_id_check(self):
        post = helpers.post()
        rule = Rule({
            'crosspost_id': post.id,
            'action': 'approve'
        })

        mod = PostModerator(post)
        self.assertFalse(mod.moderate(rule), "Post crosspost_id matching even when post is not a crosspost")

        post.crosspost_parent = 't3_'+post.id
        post.id = 'dontmatch'
        assert mod.moderate(rule), "Post crosspost_id not matching"

        post.crosspost_parent = "t3_testid"
        self.assertFalse(mod.moderate(rule), "Post crosspost_id matching as false positive")

    def test_crosspost_title_check(self):
        old_submission = reddit.submission
        og_post = helpers.post()
        reddit.submission = MagicMock(return_value=og_post)

        post = helpers.post()
        rule = Rule({
            'crosspost_title': 'Post',
            'action': 'approve'
        })

        mod = PostModerator(post)
        self.assertFalse(mod.moderate(rule), "Post crosspost_title matching even when post is not a crosspost")

        post.crosspost_parent = 't3_abcde'
        post.title = 'Dont match'
        assert mod.moderate(rule), "Post crosspost_title not matching"

        og_post.title = "Test Title"
        self.assertFalse(mod.moderate(rule), "Post crosspost_title matching as false positive")

        reddit.submission = old_submission

    def test_media_author_check(self):
        post = helpers.post()
        rule = Rule({
            'media_author': 'Tester',
            'action': 'approve'
        })

        mod = PostModerator(post)
        self.assertFalse(mod.moderate(rule), "Post media_author matching even when media is empty")

        post.media = { 'oembed': { 'author_name': 'Tester' } }
        assert mod.moderate(rule), "Post media_author not matching"

        post.media['oembed']['author_name'] = 'Notest'
        self.assertFalse(mod.moderate(rule), "Post media_author matching as a false positive")


    def test_media_author_url_check(self):
        post = helpers.post()
        rule = Rule({
            'media_author_url (full-exact)': 'https://www.example.com',
            'action': 'approve'
        })

        mod = PostModerator(post)
        self.assertFalse(mod.moderate(rule), "Post media_author_url matching even when media is empty")

        post.media = { 'oembed': { 'author_url': 'https://www.example.com' } }
        assert mod.moderate(rule), "Post media_author_url not matching"

        post.media['oembed']['author_url'] = 'https://www.noexample.com'
        self.assertFalse(mod.moderate(rule), "Post media_author_url matching as a false positive")

    def test_media_title_check(self):
        post = helpers.post()
        rule = Rule({
            'media_title': 'Hello',
            'action': 'approve'
        })

        mod = PostModerator(post)
        self.assertFalse(mod.moderate(rule), "Post media_title matching even when media is empty")

        post.media = { 'oembed': { 'title': 'Hello, World!' } }
        assert mod.moderate(rule), "Post media_title not matching"

        post.media['oembed']['title'] = 'Goodbye'
        self.assertFalse(mod.moderate(rule), "Post media_title matching as a false positive")

    def test_media_description_check(self):
        post = helpers.post()
        rule = Rule({
            'media_description': 'Hello',
            'action': 'approve'
        })

        mod = PostModerator(post)
        self.assertFalse(mod.moderate(rule), "Post media_description matching even when media is empty")

        post.media = { 'oembed': { 'description': 'Hello, World!' } }
        assert mod.moderate(rule), "Post media_description not matching"

        post.media['oembed']['description'] = 'Goodbye'
        self.assertFalse(mod.moderate(rule), "Post media_description matching as a false positive")

    def test_is_poll(self):
        rule = Rule({
            'is_poll': True,
            'action': 'approve'
        })

        class PollData:
            def __init__(self):
                self.options = [
                    'Is this a test?',
                    'Or is this just fantasy?'
                ]

        poll_data = PollData()
        post = helpers.post()
        type(post).poll_data = PropertyMock(return_value=poll_data)

        mod = PostModerator(post)
        assert mod.moderate(rule), "is_poll not matching"

        delattr(type(post), 'poll_data')
        self.assertFalse(mod.moderate(rule), "is_poll matching as false positive")

    def test_is_original_content(self):
        post = helpers.post()
        rule = Rule({
            'is_original_content': True,
            'action': 'approve'
        })

        post.is_original_content = True
        mod = PostModerator(post)
        assert mod.moderate(rule), "is_original_content not matching"

        post.is_original_content = False
        self.assertFalse(mod.moderate(rule), "is_original_content matching as false positive")

    def test_is_gallery(self):
        post = helpers.post()
        rule = Rule({
            'is_gallery': True,
            'action': 'approve'
        })

        post.is_gallery = True
        mod = PostModerator(post)
        assert mod.moderate(rule), "is_gallery not matching"

        post.is_gallery = False
        self.assertFalse(mod.moderate(rule), "is_gallery matching as false positive")

        delattr(post, 'is_gallery')
        self.assertFalse(mod.moderate(rule), "is_gallery matching when the property doesn't exist")

    def test_set_flair(self):
        post = helpers.post()
        mod = PostModerator(post)
        flair_mock = MagicMock()
        post.mod.flair = flair_mock
        post.link_flair_text = None

        # Sets text
        mod.moderate(Rule({
            'id': post.id,
            'set_flair': 'test'
        }))
        flair_mock.assert_called_with(text='test')

        # Sets both text and css
        flair_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'set_flair': ['test', 'csstest']
        }))
        flair_mock.assert_called_with(text='test', css_class='csstest')

        # Raises an exception if a dictionary is passed with no template_id
        with self.assertRaises(Exception):
            mod.moderate(Rule({
                'id': post.id,
                'set_flair': {
                    'text': 'test'
                }
            }))

        # Sets template_id, text, and css
        flair_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'set_flair': {
                'template_id': 'idtest',
                'text': 'test',
                'css_class': 'csstest'
            }
        }))
        flair_mock.assert_called_with(text='test', css_class='csstest', template_id='idtest')

        # Does not set new flair, because overwrite_flair is not set
        flair_mock.reset_mock()
        post.link_flair_text = 'before'
        mod.moderate(Rule({
            'id': post.id,
            'set_flair': 'test'
        }))
        flair_mock.assert_not_called()

        mod.moderate(Rule({
            'id': post.id,
            'set_flair': 'test',
            'overwrite_flair': True
        }))
        flair_mock.assert_called_with(text='test')

    def test_set_nsfw(self):
        post = helpers.post()
        mod = PostModerator(post)
        nsfw_mock = MagicMock()
        sfw_mock = MagicMock()
        post.mod.nsfw = nsfw_mock
        post.mod.sfw = sfw_mock

        mod.moderate(Rule({
            'id': post.id,
            'set_nsfw': True
        }))
        nsfw_mock.assert_called()
        sfw_mock.assert_not_called()

        nsfw_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'set_nsfw': False
        }))
        nsfw_mock.assert_not_called()
        sfw_mock.assert_called()

    def test_set_spoiler(self):
        post = helpers.post()
        mod = PostModerator(post)
        spoiler_mock = MagicMock()
        unspoiler_mock = MagicMock()
        post.mod.spoiler = spoiler_mock
        post.mod.unspoiler = unspoiler_mock

        mod.moderate(Rule({
            'id': post.id,
            'set_spoiler': True
        }))
        spoiler_mock.assert_called()
        unspoiler_mock.assert_not_called()

        spoiler_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'set_spoiler': False
        }))
        spoiler_mock.assert_not_called()
        unspoiler_mock.assert_called()

    def test_set_contest_mode(self):
        post = helpers.post()
        mod = PostModerator(post)
        contest_mode_mock = MagicMock()
        post.mod.contest_mode = contest_mode_mock

        mod.moderate(Rule({
            'id': post.id,
            'set_contest_mode': True
        }))
        contest_mode_mock.assert_called_with(True)

        mod.moderate(Rule({
            'id': post.id,
            'set_contest_mode': False
        }))
        contest_mode_mock.assert_called_with(False)

    def test_set_original_content(self):
        post = helpers.post()
        mod = PostModerator(post)
        set_original_content_mock = MagicMock()
        unset_original_content_mock = MagicMock()
        post.mod.set_original_content = set_original_content_mock
        post.mod.unset_original_content = unset_original_content_mock

        mod.moderate(Rule({
            'id': post.id,
            'set_original_content': True
        }))
        set_original_content_mock.assert_called()
        unset_original_content_mock.assert_not_called()

        set_original_content_mock.reset_mock()
        mod.moderate(Rule({
            'id': post.id,
            'set_original_content': False
        }))
        set_original_content_mock.assert_not_called()
        unset_original_content_mock.assert_called()

    def test_set_suggested_sort(self):
        post = helpers.post()
        mod = PostModerator(post)
        suggested_sort_mock = MagicMock()
        post.mod.suggested_sort = suggested_sort_mock

        mod.moderate(Rule({
            'id': post.id,
            'set_suggested_sort': 'hot'
        }))
        suggested_sort_mock.assert_called_with('hot')

        mod.moderate(Rule({
            'id': post.id,
            'set_suggested_sort': 'new'
        }))
        suggested_sort_mock.assert_called_with('new')

    def test_ignore_blockquotes(self):
        rule = Rule({
            'ignore_blockquotes': True
        })
        post = helpers.post()
        mod = PostModerator(post)

        # test
        #     test <-- removed
        #          <-- removed
        #     test <-- removed
        # test
        post.selftext = "test\n    test\n    \n    test\ntest"
        self.assertEqual(len(mod.checks.body.__wrapped__(mod, rule, [])), 9)

        post.selftext = "test ```test\ntest\n    test\n  test\ntest``` test"
        self.assertEqual(len(mod.checks.body.__wrapped__(mod, rule, [])), 10)

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

        mod = PostModerator(post)
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

        mod = PostModerator(post)
        og_post.subreddit.over18 = True
        self.assertFalse(mod.moderate(rule), "crosspost_subreddit is_nsfw matching even when post is not a crosspost")

        post.crosspost_parent = 't3_abcde'
        assert mod.moderate(rule), "crosspost_subreddit is_nsfw not matching"

        og_post.subreddit.over18 = False
        self.assertFalse(mod.moderate(rule), "crosspost_subreddit is_nsfw matching as false positive")

        reddit.submission = old_submission
