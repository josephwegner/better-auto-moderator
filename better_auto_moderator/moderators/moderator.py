import re
import praw
from urllib.parse import urlparse
from functools import cached_property, wraps
from better_auto_moderator.rule import Rule
from better_auto_moderator.reddit import reddit
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Moderator:
    moderators_exempt_actions = [
        'remove',
        'report',
        'spam',
        'filter'
    ]

    def __init__(self, item):
        self.item = item
        self.matches = {}

    def set_match(self, match, value):
        self.matches[match] = value

    # Available at `self.checks`, without needing to call the func
    @cached_property
    def checks(self):
        return ModeratorChecks(self)

    # Available at `self.actions`, without needing to call the func
    @cached_property
    def actions(self):
        return ModeratorActions(self)

    def are_moderators_exempt(self, rule):
        exempt = False
        if rule.config.get('action') in self.moderators_exempt_actions:
            exempt = True

        if 'moderators_exempt' in rule.config:
            exempt = rule.config['moderators_exempt']

        return exempt

    def moderate(self, rule):
        if self.are_moderators_exempt(rule):
            if self.item.subreddit in self.item.author.moderated():
                return False

        # Run all of the checks in this rule to see if the item matches
        if not self.check(rule):
            return False

        return self.action(rule)

    # actions can be set specifically here, if you want to run tests on a sub-group, like "author"
    # If it's not defined, we'll use whatever is defined in the `actions` method
    def action(self, rule, actions=None):
        if actions is None:
            actions = self.actions

        ran = False
        for key in rule.config.keys():
            if hasattr(actions, key):
                if getattr(actions, key)(rule):
                    ran = True

        return ran

    # checks can be set specifically here, if you want to run tests on a sub-group, like "author"
    # If it's not defined, we'll use whatever is defined in the `checks` method
    def check(self, rule, checks=None):
        if checks is None:
            checks = self.checks

        satisfy_any_threshold = rule.config.get('satisfy_any_threshold')
        satisfied_threshold = False
        threshold_checks = ['comment_karma', 'post_karma', 'combined_karma', 'account_age']

        for key in rule.config:
            check_name = key
            # Search for options, like (regex) or (case-sensitive)
            options_re = re.search(r'.*\(([a-z, \-]+)\)', key)
            options = []
            if options_re is not None:
                # Strip whitespace off the options, and remove them from check_name
                options = [opt.strip() for opt in options_re.group(1).split(',')]
                check_name = re.search(r'([^\s]*)\s?\(', key).group(1)

            # Checks can have a ~ before them to indicate match IF THIS RULE IS FALSE.
            check_truthiness = True
            if check_name[0] == '~':
                check_name = check_name[1:]
                check_truthiness = False

            # Checks can be combined, like `body+author: butts`. These are OR conditions, not AND
            passed = False
            for name in check_name.split('+'):
                if not hasattr(checks, name):
                    passed = True
                    break

                check = getattr(checks, name)
                if callable(check):
                    values = rule.config[key]
                    # Multiple values can be passed in, as an array. We should force single values
                    # into an "array", just so the code runs in a similar way regardless
                    # of inputs
                    if not isinstance(values, list):
                        values = [values]

                    for val in values:
                        if isinstance(val, str):
                            val = ModeratorPlaceholders.replace(val, self.item, self)

                        check_val = check(val, rule, options)
                        if check_val is None:
                            return False
                        elif check_val is check_truthiness:
                            passed = True

            if not passed and (not satisfy_any_threshold or check_name not in threshold_checks):
                return False
            elif passed and satisfy_any_threshold and check_name in threshold_checks:
                satisfied_threshold = True

        if satisfy_any_threshold:
            return satisfied_threshold

        # None of checks failed, so this must be a pass!
        return True

    @staticmethod
    def full_exact(values, test, options):
        if not isinstance(values, list):
            values = [values]

        values = [value for value in values if value is not None]

        if 'regex' in options:
            for value in values:
                if re.fullmatch(test, value) is not None:
                    return True

            return False

        if not 'case-sensitive' in options:
            values = [value.lower() for value in values]
            test = test.lower()

        for value in values:
            if value == test:
                return True

        return False

    @staticmethod
    def includes(values, test, options):
        if not isinstance(values, list):
            values = [values]

        values = [value for value in values if value is not None]

        if 'regex' in options:
            for value in values:
                if re.match(test, value) is not None:
                    return True

            return False

        if not 'case-sensitive' in options:
            values = [value.lower() for value in values]
            test = test.lower()

        for value in values:
            if test in value:
                return True

        return False

    @classmethod
    def includes_word(cls, value, test, options):
        words = re.findall(r'\w+', value)
        for word in words:
            if cls.full_exact(word, test, options):
                return True

        return False

    @classmethod
    def ends_with(cls, value, test, options):
        if 'regex' in options:
            raise Exception("ends_with comparator can not use the regex option")

        length = len(test)
        chars = value[length * -1 :]
        return cls.full_exact(chars, test, options)


    @classmethod
    def starts_with(cls, value, test, options):
        if 'regex' in options:
            raise Exception("ends_with comparator can not use the regex option")

        length = len(test)
        chars = value[: length]
        return cls.full_exact(chars, test, options)

    @staticmethod
    def time(value, test, options):
        number = float(re.search(r'[0-9\-.]+', test).group(0))
        delta = None

        if 'minutes' in test:
            delta = relativedelta(minutes=number) # Do nothing, unit is minutes
        elif 'hours' in test:
            delta = relativedelta(hours=number)
        elif 'weeks' in test:
            delta = relativedelta(weeks=number)
        elif 'years' in test:
            delta = relativedelta(years=number)
        elif 'months' in test:
            delta = relativedelta(months=number)
        else: # Default is days
            delta = relativedelta(days=number)

        comparison_time = value + delta
        now = datetime.utcfromtimestamp(datetime.today().timestamp())

        if '>=' in test or 'greater-than-equal' in options:
            return now >= comparison_time
        elif '<=' in test or 'less-than-equal' in options:
            return now <= comparison_time
        if '>' in test or 'greater-than' in options:
            return now > comparison_time
        elif '<' in test or 'less-than' in options:
            return now < comparison_time
        else:
            return now == comparison_time

    @classmethod
    def full_text(cls, value, test, options):
        value = re.sub(r'^[^A-Za-z0-9]*', '', value)
        value = re.sub(r'[^A-Za-z0-9]*$', '', value)
        return cls.full_exact(value, test, options)

    @staticmethod
    def numeric(value, test, options):
        test = str(test)
        # Pull the numeric value out of the test string
        number = float(re.search(r'[0-9\-.]+', test).group(0))
        if '>=' in test or 'greater-than-equal' in options:
            return value >= number
        elif '<=' in test or 'less-than-equal' in options:
            return value <= number
        if '>' in test or 'greater-than' in options:
            return value > number
        elif '<' in test or 'less-than' in options:
            return value < number
        else:
            return value == number

    @staticmethod
    def bool(value, test, options):
        return value is test

# We're going to wrap all the getters with this decorator, which figures out how
# to compare the values
def comparator(default='full-exact', **kwargs):
    def decorator_comparator(func):
        @wraps(func)
        def wrapper_comparator(inst, value, rule, options):
            comparator = getattr(inst.moderator, default.replace('-', '_'))
            # Check if any of the options are actually comparators
            for option in options:
                if hasattr(inst.moderator, option.replace('-', '_')):
                    comparator = getattr(inst.moderator, option.replace('-', '_'))

            # Allow comparators to set a value that will automatically cause the check to be skipped
            func_value = func(inst, rule, options)
            # Store the value in the moderator, so it can be used by placeholders
            inst.moderator.set_match(func.__name__, func_value)
            if 'skip_if' in kwargs and kwargs.get('skip_if') == func_value:
                return None

            return comparator(func_value, value, options)
        return wrapper_comparator
    return decorator_comparator

class AbstractChecks:
    def __init__(self, moderator):
        self.moderator = moderator
        self.item = moderator.item

class ModeratorChecks(AbstractChecks):
    @comparator(default='full-exact', skip_if=None)
    def id(self, rule, options):
        return self.item.id

    @comparator(default='includes-word')
    def body(self, rule, options):
        body = self.item.body
        if rule.config.get('ignore_blockquotes'):
            tick_match = re.compile(r'```.*?```', re.DOTALL)
            body = re.sub(tick_match, '', body)
            body = re.sub(r'    [^\n]*\n', '', body)

        return body

    @comparator(default='numeric')
    def body_longer_than(self, rule, options):
        options.append('greater-than')
        body = self.body.__wrapped__(self, rule, options)

        body = re.sub(r'^[^A-Za-z0-9]*', '', body)
        body = re.sub(r'[^A-Za-z0-9]*$', '', body)

        return len(body)

    @comparator(default='numeric')
    def body_shorter_than(self, rule, options):
        options.append('less-than')
        body = self.body.__wrapped__(self, rule, options)

        body = re.sub(r'^[^A-Za-z0-9]*', '', body)
        body = re.sub(r'[^A-Za-z0-9]*$', '', body)

        return len(body)

    @comparator(default='includes')
    def url(self, rule, options):
        if hasattr(self.item, 'crosspost_parent'):
            return reddit.submission(self.item.crosspost_parent.split('_')[1]).url

        return self.item.url

    def author(self, value, rule, options):
        author_checks = ModeratorAuthorChecks(self.moderator)
        author_rule = Rule(value)
        return self.moderator.check(author_rule, checks=author_checks)

    def crosspost_author(self, value, rule, options):
        if not hasattr(self.item, 'crosspost_parent'):
            return None

        author_checks = ModeratorAuthorChecks(self.moderator)
        author_checks.item = reddit.submission(self.item.crosspost_parent.split('_')[1])
        author_rule = Rule(value)
        return self.moderator.check(author_rule, checks=author_checks)

    def crosspost_subreddit(self, value, rule, options):
        if not hasattr(self.item, 'crosspost_parent'):
            return None

        sub_checks = ModeratorCrosspostSubredditChecks(self.moderator)
        sub_rule = Rule(value)
        return self.moderator.check(sub_rule, checks=sub_checks)

    @comparator(default='contains')
    def report_reason(self, rule, options):
        reports = self.item.user_reports
        if not self.moderator.are_moderators_exempt(rule):
            reports = reports + self.item.mod_reports

        return [report[0] for report in reports]

    @comparator(default='numeric')
    def reports(self, rule, options):
        options.append('greater-than-equal')
        return len(self.item.user_reports) + len(self.item.mod_reports)

    @comparator(default='bool')
    def is_edited(self, rule, options):
        return self.item.edited

class ModeratorCrosspostSubredditChecks(AbstractChecks):
    @cached_property
    def parent(self):
        return reddit.submission(self.item.crosspost_parent.split('_')[1])

    @comparator(default='includes-word')
    def name(self, rule, options):
        return self.parent.subreddit.name

    @comparator(default='bool')
    def is_nsfw(self, rule, options):
        return self.parent.subreddit.over18

class ModeratorAuthorChecks(AbstractChecks):
    @comparator(default='numeric')
    def comment_karma(self, rule, options):
        return self.item.author.comment_karma

    @comparator(default='numeric')
    def post_karma(self, rule, options):
        return self.item.author.link_karma

    @comparator(default='numeric')
    def combined_karma(self, rule, options):
        return self.item.author.link_karma + self.item.author.comment_karma

    @comparator(default='full-exact')
    def id(self, rule, options):
        return self.item.author.id

    @comparator(default='includes-word')
    def id(self, rule, options):
        return self.item.author.name

    @comparator(default='full-exact')
    def flair_template_id(self, rule, options):
        url = "r/%s/api/flairselector?name=%s" % (self.item.subreddit.name, self.item.author.name)
        flair = reddit.post(url)['current']
        if 'flair_template_id' in flair:
            return flair['flair_template_id']
        else:
            return ''

    @comparator(default='full-exact')
    def flair_text(self, rule, options):
        return next(self.item.subreddit.flair(self.item.author.name))['flair_text']

    @comparator(default='full-exact')
    def flair_css_class(self, rule, options):
        return next(self.item.subreddit.flair(self.item.author.name))['flair_css_class']

    @comparator(default='time')
    def account_age(self, rule, options):
        return datetime.utcfromtimestamp(self.item.author.created_utc)

    @comparator(default='bool')
    def is_gold(self, rule, options):
        return self.item.author.is_gold

    @comparator(default='bool')
    def is_contributor(default='bool'):
        return any(self.item.subreddit.contributor(redditor=self.item.author.name))

    @comparator(default='bool')
    def is_moderator(default='bool'):
        return any(self.item.subreddit.moderator(redditor=self.item.author.name))

class AbstractActions:
    def __init__(self, moderator):
        self.moderator = moderator
        self.item = moderator.item

class ModeratorActions(AbstractActions):
    def author(self, rule):
        author_actions = ModeratorAuthorActions(self.moderator)
        author_rule = Rule(rule.config.get('author'))
        return self.moderator.action(author_rule, actions=author_actions)

    def crosspost_author(self, value, rule, options):
        if not hasattr(self.item, 'crosspost_parent'):
            return None

        author_actions = ModeratorAuthorActions(self.moderator)
        author_actions.item = reddit.submission(self.item.crosspost_parent.split('_')[1])
        author_rule = Rule(value)
        return self.moderator.check(author_rule, actions=author_actions)

    def ignore_reports(self, rule):
        print("Ingoring reports on %s %s" % (type(self.item).__name__, self.item.id))
        self.item.mod.ignore_reports()
        return True

    def reply(self, rule):
        body = rule.config['reply']
        print("Replying to %s %s" % (type(self.item).__name__, self.item.id))
        comment = self.item.reply(body)

        if rule.config.get('comment_locked'):
            comment.lock()
        if rule.config.get('comment_stickied'):
            self.item.mod.distinguish("yes", sticky=True)

    def message(self, rule):
        subject = "BetterAutoModerator notification"
        if 'message_subject' in rule.config:
            subject = rule.config['message_subject']

        message = "%s\n%s\nI am a bot, and this action was"\
        "performed automatically. Please [contact the moderators of this subreddit]"\
        "(https://www.reddit.com/message/compose/?to=/r/%s) if you have"\
        "any questions or concerns." % (self.item.permalink, rule.config['message'], self.item.subreddit.name)

        self.item.author.message(subject, message)

    def modmail(self, rule):
        subject = "BetterAutoModerator notification"
        if 'modmail_subject' in rule.config:
            subject = rule.config['modmail_subject']

        message = "%s\n%s\nI am a bot, and this action was"\
        "performed automatically." % (self.item.permalink, rule.config['message'])

        self.item.subreddit.modmail.create(subject, message, reddit.user)

    def action(self, rule):
        value = rule.config['action']
        if 'action_reason' in rule.config and value != 'report':
            print("Note: action_reason cannot be attached to rules enforced by BAM. Logging instead: %s" % rule.config['action_reason'])

        if value == 'approve':
            if self.item.removed:
                return False

            if self.item.approved and 'reports' not in rule.config:
                return False

            print("Approving %s %s" % (type(self.item).__name__, self.item.id))
            self.item.mod.approve()
            return True

        elif value == 'remove':
            if self.item.approved:
                return False

            print("Removing %s %s" % (type(self.item).__name__, self.item.id))
            self.item.mod.remove()
            return True

        elif value == 'spam':
            print("Marking %s %s as spam" % (type(self.item).__name__, self.item.id))
            self.item.mod.remove(spam=True)
            return True

        elif value == 'report':
            print("Reporting %s %s" % (type(self.item).__name__, self.item.id))
            reason = None
            if 'report_reason' in rule.config:
                reason = rule.config['report_reason']
            elif 'action_reason' in rule.config:
                reason = rule.config['action_reason']

            self.item.report(reason)
            return True

        return False

    def set_sticky(self, rule):
        value = rule.config.get('set_sticky')
        if value:
            print("Setting %s %s to sticky" % (type(self.item).__name__, self.item.id))
            self.item.mod.distinguish("yes", sticky=True)
        else:
            print("Setting %s %s to not sticky" % (type(self.item).__name__, self.item.id))
            self.item.mod.distinguish("no", sticky=False)

        return True

    def set_locked(self, rule):
        value = rule.config['set_locked']
        if value:
            print("Locking %s %s" % (type(self.item).__name__, self.item.id))
            self.item.mod.lock()
        else:
            print("Unlocking %s %s" % (type(self.item).__name__, self.item.id))
            self.item.mod.unlock()

        return True

class ModeratorAuthorActions(AbstractActions):
    def set_flair(self, rule):
        check = ModeratorAuthorChecks(self.moderator)
        flair_text = check.flair_text.__wrapped__(check, rule, [])

        if(flair_text is None or rule.config.get('overwrite_flair')):
            print("Setting flair for user %s" % self.item.author.name)
            value = rule.config['set_flair']
            if isinstance(value, str):
                self.item.subreddit.flair.set(text=value)
                return True
            elif isinstance(value, list):
                self.item.subreddit.flair.set(text=value[0], css_class=value[1])
                return True
            elif isinstance(value, dict):
                if not 'template_id' in value:
                    raise Exception("template_id must be provided in set_flair object")

                self.item.subreddit.flair.set(text=value['text'], css_class=value['css_class'], template_id=value['template_id'])
                return True

        return False

class ModeratorPlaceholders():
    @classmethod
    def replace(cls, str, item, mod):
        # Find anything like {{word}} in the string
        match = re.search(r'{{(.*?)}}', str)
        if match is None:
            return str

        replaced = str
        for group in match.groups():
            inject = None
            if group[:5] == 'match':
                key = group[6:]
                if key == '':
                    key = None
                inject = cls.match(mod, key=key)
            elif hasattr(cls, group): # If a placeholder exists, use it!
                inject = getattr(cls, group)(item)

            if inject is not None:
                replaced = str.replace("{{%s}}" % group, inject)

        return replaced

    @staticmethod
    def match(mod, key=None):
        if key is None:
            if len(mod.matches.keys()) == 0:
                return None
            key = mod.matches.keys()[0]

        if key in mod.matches:
            return mod.matches[key]
        else:
            return None

    @staticmethod
    def author(item):
        return str(item.author.name)

    @staticmethod
    def author_flair_text(item):
        return next(item.subreddit.flair(item.author.name))['flair_text']

    @staticmethod
    def author_flair_css_class(item):
        return next(item.subreddit.flair(item.author.name))['flair_css_class']

    @staticmethod
    def author_flair_template_id(item):
        url = "r/%s/api/flairselector?name=%s" % (item.subreddit.name, item.author.name)
        flair = reddit.post(url)['current']
        if 'flair_template_id' in flair:
            return flair['flair_template_id']
        else:
            return ''

    @staticmethod
    def body(item):
        if hasattr(item, 'body'):
            return item.body
        elif hasattr(item, 'crosspost_parent'):
            return reddit.submission(item.crosspost_parent.split('_')[1]).selftext
        elif hasattr(item, 'selftext'):
            return item.body

    @staticmethod
    def permalink(item):
        return "https://www.reddit.com%s" % item.permalink

    @staticmethod
    def subreddit(item):
        return item.subreddit.name

    @staticmethod
    def kind(item):
        if isinstance(item, praw.models.Submission):
            return 'submission'
        elif isinstance(item, praw.models.Comment):
            return 'comment'
        elif isinstance(item, praw.models.SubredditMessage):
            return 'modmail'

        return None

    @staticmethod
    def title(item):
        if hasattr(item, 'title'):
            return item.title

        return None

    @staticmethod
    def domain(item):
        if hasattr(item, 'url'):
            url = urlparse(item.url)
            if url.netloc != 'www.reddit.com':
                return url.netloc

        return "self.%s" % item.subreddit.name

    @staticmethod
    def url(item):
        if hasattr(item, 'url'):
            return item.url

        return None

    @staticmethod
    def media_author(item):
        if self.item.media is not None:
            if 'oembed' in self.item.media and 'author_name' in self.item.media['oembed']:
                return self.item.media['oembed']['author_name']
            else:
                return ''
        else:
            return None

    @staticmethod
    def media_author_url(item):
        if self.item.media is not None:
            if 'oembed' in self.item.media and 'author_url' in self.item.media['oembed']:
                return self.item.media['oembed']['author_url']
            else:
                return ''
        else:
            return None

    @staticmethod
    def media_title(item):
        if self.item.media is not None:
            if 'oembed' in self.item.media and 'title' in self.item.media['oembed']:
                return self.item.media['oembed']['title']
            else:
                return ''
        else:
            return None

    @staticmethod
    def media_description(item):
        if self.item.media is not None:
            if 'oembed' in self.item.media and 'description' in self.item.media['oembed']:
                return self.item.media['oembed']['description']
            else:
                return ''
        else:
            return None
