from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, comparator

class ModqueueModerator(Moderator):

    @cached_property
    def checks(self):
        return ModqueueModeratorChecks(self)

    def are_moderators_exempt(self, rule):
        exempt = False
        if 'moderators_exempt' in rule.config:
            exempt = rule.config['moderators_exempt']

        return exempt

    @classmethod
    def contains(cls, values, test, options):
        for value in values:
            # use full_exact, so options like case-sensitive and regexp still work
            if cls.full_exact(value, test, options):
                return True

        return False

    @classmethod
    def only(cls, values, test, options):
        if len(values) == 0:
            return False

        for value in values:
            # use full_exact, so options like case-sensitive and regexp still work
            if not cls.full_exact(value, test, options):
                return False

        return True


class ModqueueModeratorChecks(ModeratorChecks):
    @comparator(default='contains')
    def report_reason(self, rule, options):
        reports = self.item.user_reports
        if not self.moderator.are_moderators_exempt(rule):
            reports = reports + self.item.mod_reports

        return [report[0] for report in reports]
