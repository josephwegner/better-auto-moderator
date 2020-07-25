from functools import cached_property
from better_auto_moderator.moderators.moderator import Moderator, ModeratorChecks, ModeratorAuthorChecks, comparator
from better_auto_moderator.rule import Rule

class CommentModerator(Moderator):
    @cached_property
    def checks(self):
        return CommentModeratorChecks(self)

class CommentModeratorChecks(ModeratorChecks):
    def author(self, value, rule, options):
        author_checks = ModeratorCommentAuthorChecks(self.moderator)
        author_rule = Rule(value)
        return self.moderator.check(author_rule, checks=author_checks)

    @comparator(default='bool')
    def is_top_level(self, rule, options):
        return self.item.depth == 0

class ModeratorCommentAuthorChecks(ModeratorAuthorChecks):
    @comparator(default='bool')
    def is_submitter(self, rule, options):
        return self.item.author.id == self.item.submission.author.id
