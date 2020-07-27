import re
from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, ModeratorActions, comparator
from better_auto_moderator.reddit import reddit

class PostModerator(Moderator):
    @cached_property
    def actions(self):
        return PostModeratorActions(self)

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
        body = ""
        if hasattr(self.item, 'crosspost_parent'):
            body = reddit.submission(self.item.crosspost_parent.split('_')[1]).selftext
        else:
            body = self.item.selftext

        if rule.config.get('ignore_blockquotes'):
            tick_match = re.compile(r'```.*?```', re.DOTALL)
            body = re.sub(tick_match, '', body)
            body = re.sub(r'    [^\n]*\n', '', body)

        return body

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

class PostModeratorActions(ModeratorActions):
    def set_flair(self, rule):
        if(self.item.link_flair_text is None or rule.config.get('overwrite_flair')):
            print("Setting flair for user %s" % self.item.author.name)
            value = rule.config['set_flair']
            if isinstance(value, str):
                self.item.mod.flair(text=value)
                return True
            elif isinstance(value, list):
                self.item.mod.flair(text=value[0], css_class=value[1])
                return True
            elif isinstance(value, dict):
                if not 'template_id' in value:
                    raise Exception("template_id must be provided in set_flair object")

                self.item.mod.flair(text=value['text'], css_class=value['css_class'], template_id=value['template_id'])
                return True

        return False

    def set_nsfw(self, rule):
        value = rule.config['set_nsfw']
        if value:
            print("Setting %s %s as nsfw" % (type(self.item).__name__, self.item.id))
            self.item.mod.nsfw()
        else:
            print("Setting %s %s as sfw" % (type(self.item).__name__, self.item.id))
            self.item.mod.sfw()

        return True

    def set_spoiler(self, rule):
        value = rule.config['set_spoiler']
        if value:
            print("Setting %s %s as spoiler" % (type(self.item).__name__, self.item.id))
            self.item.mod.spoiler()
        else:
            print("Removing spoiler tag from %s %s" % (type(self.item).__name__, self.item.id))
            self.item.mod.unspoiler()

        return True

    def set_contest_mode(self, rule):
        print("Setting contest mode on %s %s" % (type(self.item).__name__, self.item.id))
        self.item.mod.contest_mode((rule.config['set_contest_mode'] is True))
        return True

    def set_original_content(self, rule):
        value = rule.config['set_original_content']
        if value:
            print("Setting %s %s as original content" % (type(self.item).__name__, self.item.id))
            self.item.mod.set_original_content()
        else:
            print("Unsetting %s %s as original content" % (type(self.item).__name__, self.item.id))
            self.item.mod.unset_original_content()

        return True

    def set_suggested_sort(self, rule):
        print("Setting suggested sort on %s %s to %s" % (type(self.item).__name__, self.item.id, rule.config['set_suggested_sort']))
        self.item.mod.suggested_sort(rule.config['set_suggested_sort'])
        return True
