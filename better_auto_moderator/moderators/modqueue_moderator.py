import pprint
from better_auto_moderator.moderators.moderator import Moderator

class ModqueueModerator(Moderator):

    checks = { **Moderator.checks,
        'report_reason': {
            'comparison': 'contains',
            'get': lambda item: [report[0] for report in item.user_reports]
        }
    }

    def __init__(self, item):
        super().__init__(item)

    def are_moderators_exempt(self, rule):
        exempt = False
        if 'moderators_exempt' in rule.config:
            exempt = rule.config['moderators_exempt']

        return exempt

    @staticmethod
    def contains(values, test):
        for value in values:
            if Moderator.full_exact(value, test):
                return True

        return False

    @staticmethod
    def only(values, test):
        if len(values) == 0:
            return False

        for value in values:
            if not Moderator.full_exact(value, test):
                return False

        return True
