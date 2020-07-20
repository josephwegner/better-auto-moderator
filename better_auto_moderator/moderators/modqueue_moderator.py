import pprint
from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, comparator

class ModqueueModerator(Moderator):
    def __init__(self, item):
        super().__init__(item)

    @cached_property
    def checks(self):
        return ModqueueModeratorChecks(self)

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


class ModqueueModeratorChecks(ModeratorChecks):
    @comparator(default='contains')
    def report_reason(self, rule, options):
        reports = self.item.user_reports
        if not self.moderator.are_moderators_exempt(rule):
            reports = reports + self.item.mod_reports

        return [report[0] for report in reports]
