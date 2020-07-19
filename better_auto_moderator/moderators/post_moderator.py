from better_auto_moderator.moderators.moderator import Moderator

"""
    submission_checks = {
        'id',
        'title',
        'domain',
        'url',
        'body',
        'flair_text',
        'flair_css_class',
        'flair_template_id',
        'poll_option_text',
        'poll_option_count',
        'domain',
        'crosspost_id',
        'crosspost_title',
        'media_author',
        'media_author_url',
        'media_title',
        'media_description'
        'is_original_content'
        'is_poll'
        'is_gallery'
    }
"""

class PostModerator(Moderator):
    def __init__(self, item):
        super().__init__(item)
