from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, comparator

class ModqueueModerator(Moderator):
    def are_moderators_exempt(self, rule):
        exempt = False
        if 'moderators_exempt' in rule.config:
            exempt = rule.config['moderators_exempt']

        return exempt
