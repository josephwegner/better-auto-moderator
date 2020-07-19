import re

class Moderator:
    moderators_exempt_actions = [
        'remove',
        'report',
        'spam',
        'filter'
    ]

    checks = {
        'id': {
            'comparison': 'full-exact',
            'get': lambda item: item.id
        }
    }

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
            print("Actoon %s invoked, but is not implemented" % action)
            return False

        actioner = getattr(self, self.actions[action])
        actioner(rule)

        return True

    def check(self, rule):
        for key in rule.config:
            check = key
            options_re = re.search(r'.*\(([a-z, ]+)\)', key)
            options = []
            if options_re is not None:
                options = [opt.strip() for opt in options_re.group(1).split(',')]
                check = re.search(r'([^\s]*)\s?\(', key).group(1)

            if check in self.checks:
                check = self.checks[check]
                comparison_key = check['comparison'].replace('-', '_')

                for option in options:
                    if hasattr(self, option.replace('-', '_')):
                        comparison_key = option.replace('-', '_')

                if hasattr(self, comparison_key):
                    comparison = getattr(self, comparison_key)
                    if not comparison(check['get'](self.item), rule.config[key]):
                        return False
                else:
                    print ("Comparison %s was used, but is not implemented." % check['comparison'])
                    return False

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
    def full_exact(value, test):
        return value == test
