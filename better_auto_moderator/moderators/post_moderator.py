from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, comparator
from better_auto_moderator.reddit import reddit

class PostModerator(Moderator):

    @cached_property
    def checks(self):
        return PostModeratorChecks(self)

    @classmethod
    def domain(cls, value, test, options):
        if cls.full_exact(value, test, options):
            return True

        domain = ".%s" % test
        return cls.ends_with(value, domain, options)

class PostModeratorChecks(ModeratorChecks):
    @comparator(default='includes-word')
    def body(self,rule, options):
        if hasattr(self.item, 'crosspost_parent'):
            return reddit.submission(self.item.crosspost_parent.split('_')[1]).selftext

        return self.item.selftext

    @comparator(default='includes-word')
    def title(self, rule, options):
        return self.item.title

    @comparator(default='domain')
    def domain(self, rule, options):
        if hasattr(self.item, 'crosspost_parent'):
            return reddit.submission(self.item.crosspost_parent.split('_')[1]).domain

        return self.item.domain


    @comparator(default='full-exact')
    def flair_text(self, rule, options):
        return self.item.link_flair_text

    # Not implemented after here
    @comparator(default='full-exact')
    def flair_css_class(self, rule, options):
        return self.item.link_flair_css_class

    @comparator(default='full-exact')
    def flair_template_id(self, rule, options):
        if hasattr(self.item, 'link_flair_template_id'):
            return self.item.link_flair_template_id
        else:
            return None

    @comparator(default='includes-word')
    def poll_option_text(self, rule, options):
        if hasattr(self.item, 'poll_data'):
            return self.item.poll_data.options
        else:
            return 0

    @comparator(default='numeric')
    def poll_option_count(self, rule, options):
        if hasattr(self.item, 'poll_data'):
            return len(self.item.poll_data.options)
        else:
            return 0

    @comparator(default='includes-word', skip_if=None)
    def crosspost_id(self, rule, options):
        if hasattr(self.item, 'crosspost_parent'):
            return self.item.crosspost_parent.split('_')[1]
        else:
            return None

    @comparator(default='includes-word', skip_if=None)
    def crosspost_title(self, rule, options):
        if hasattr(self.item, 'crosspost_parent'):
            return reddit.submission(self.item.crosspost_parent.split('_')[1]).title
        else:
            return None

    @comparator(default='full-exact', skip_if=None)
    def media_author(self, rule, options):
        if self.item.media is not None:
            if 'oembed' in self.item.media and 'author_name' in self.item.media['oembed']:
                return self.item.media['oembed']['author_name']
            else:
                return ''
        else:
            return None

    @comparator(default='includes', skip_if=None)
    def media_author_url(self, rule, options):
        if self.item.media is not None:
            if 'oembed' in self.item.media and 'author_url' in self.item.media['oembed']:
                return self.item.media['oembed']['author_url']
            else:
                return ''
        else:
            return None

    @comparator(default='includes-word', skip_if=None)
    def media_title(self, rule, options):
        if self.item.media is not None:
            if 'oembed' in self.item.media and 'title' in self.item.media['oembed']:
                return self.item.media['oembed']['title']
            else:
                return ''
        else:
            return None

    @comparator(default='includes-word', skip_if=None)
    def media_description(self, rule, options):
        if self.item.media is not None:
            if 'oembed' in self.item.media and 'description' in self.item.media['oembed']:
                return self.item.media['oembed']['description']
            else:
                return ''
        else:
            return None

    @comparator(default='bool')
    def is_original_content(self, rule, options):
        return self.item.is_original_content


    @comparator(default='bool')
    def is_poll(self, rule, options):
        return hasattr(self.item, 'poll_data')

    @comparator(default='bool')
    def is_gallery(self, item, options):
        return hasattr(self.item, 'is_gallery') and self.item.is_gallery
