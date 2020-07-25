import re
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

    actions = {
        'approve': 'approve',
        'remove': 'remove'
    }

    def __init__(self, item):
        self.item = item

    # Available at `self.checks`, without needing to call the func
    @cached_property
    def checks(self):
        return ModeratorChecks(self)

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

        if 'action' not in rule.config:
            print("No action defined, skipping rule for item %s" % self.item.id)
            return False
        action = rule.config['action']

        if not action in self.actions:
            print("Action %s invoked, but not defined" % action)
            return False

        if not hasattr(self, self.actions[action]):
            print("Action %s invoked, but is not implemented" % action)
            return False

        actioner = getattr(self, self.actions[action])
        actioner(rule)

        return True

    # checks can be set specifically here, if you want to run tests on a sub-group, like "author"
    # If it's not defined, we'll use whatever is defined in the `checks` method
    def check(self, rule, checks=None):
        if checks is None:
            checks = self.checks

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
                            val = ModeratorPlaceholders.replace(val, self.item)

                        check_val = check(val, rule, options)
                        if check_val is None:
                            return False
                        elif check_val is check_truthiness:
                            passed = True
            if not passed:
                return False

        # None of checks failed, so this must be a pass!
        return True

    def approve(self, rule):
        print("Approving %s %s" % (type(self.item).__name__, self.item.id))
        self.item.mod.approve()

        if rule.config.get('ignore_reports'):
            self.item.mod.ignore_reports()

    def remove(self, rule):
        print("Removing %s %s" % (type(self.item).__name__, self.item.id))
        self.item.mod.remove()

        if rule.config.get('ignore_reports'):
            self.item.mod.ignore_reports()

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
        return self.item.body

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
        return self.item.subreddit.flair(self.item.author.name)['flair_text']

    @comparator(default='full-exact')
    def flair_css_class(self, rule, options):
        return self.item.subreddit.flair(self.item.author.name)['flair_css_class']

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

class ModeratorPlaceholders():
    @classmethod
    def replace(cls, str, item):
        # Find anything like {{word}} in the string
        match = re.search(r'{{(.*?)}}', str)
        if match is None:
            return str

        replaced = str
        for group in match.groups():
            # If a placeholder exists, use it!
            if hasattr(cls, group):
                inject = getattr(cls, group)(item)
                replaced = str.replace("{{%s}}" % group, inject)

        return replaced

    @staticmethod
    def author(item):
        return str(item.author.name)
