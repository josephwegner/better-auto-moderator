import re
from functools import cached_property, wraps
from better_auto_moderator.rule import Rule

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

    """
        global_checks = {
            'id',
            'body'
            'reports'
            'body_longer_than'
            'body_shorter_than'
            'is_edited'
        }
    """

    def __init__(self, item):
        self.item = item

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

        if not self.check(rule):
            return False

        if 'action' not in rule.config:
            print("No rule defined, skipping action for item %s" % self.item.id)
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

    def check(self, rule, checks=None):
        if checks is None:
            checks = self.checks

        for key in rule.config:
            check_name = key
            options_re = re.search(r'.*\(([a-z, \-]+)\)', key)
            options = []
            if options_re is not None:
                options = [opt.strip() for opt in options_re.group(1).split(',')]
                check_name = re.search(r'([^\s]*)\s?\(', key).group(1)

            check_truthiness = True
            if check_name[0] == '~':
                check_name = check_name[1:]
                check_truthiness = False

            for name in check_name.split('+'):
                check = getattr(checks, name)
                if callable(check):
                    val = rule.config[key]
                    if isinstance(val, str):
                        val = ModeratorPlaceholders.replace(val, self.item)

                    if check(val, rule, options) is check_truthiness:
                        return True

            return False

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
    def full_exact(value, test, options):
        if 'case-sensitive' in options:
            return value == test
        else:
            return value.lower() == test.lower()

    @staticmethod
    def numeric(value, test, options):
        number = float(re.search(r'[0-9\-.]+', test).group(0))
        if '>' in test:
            return value > number
        elif '<' in test:
            return value < number
        else:
            return value == number


def comparator(default='full-exact'):
    def decorator_comparator(func):
        wraps(func)
        def wrapper_comparator(inst, value, rule, options):
            comparator = getattr(inst.moderator, default.replace('-', '_'))
            for option in options:
                if hasattr(inst.moderator, option.replace('-', '_')):
                    comparator = getattr(inst.moderator, option.replace('-', '_'))

            return comparator(func(inst, rule, options), value, options)
        return wrapper_comparator
    return decorator_comparator

class AbstractChecks:
    def __init__(self, moderator):
        self.moderator = moderator
        self.item = moderator.item

class ModeratorChecks(AbstractChecks):
    @comparator(default='full-exact')
    def id(self, rule, options):
        return self.item.id

    @comparator(default='full-exact')
    def body(self, rule, options):
        return self.item.body

    def author(self, value, rule, options):
        author_checks = ModeratorAuthorChecks(self.moderator)
        author_rule = Rule(value)
        return self.moderator.check(author_rule, checks=author_checks)


class ModeratorAuthorChecks(AbstractChecks):
    @comparator(default='numeric')
    def post_karma(self, rule, options):
        return self.item.author.link_karma

class ModeratorPlaceholders():
    @classmethod
    def replace(cls, str, item):
        match = re.search(r'{{(.*?)}}', str)
        if match is None:
            return str

        replaced = str
        for group in match.groups():
            if hasattr(cls, group):
                inject = getattr(cls, group)(item)
                replaced = str.replace("{{%s}}" % group, inject)

        return replaced

    @staticmethod
    def author(item):
        return str(item.author.name)
