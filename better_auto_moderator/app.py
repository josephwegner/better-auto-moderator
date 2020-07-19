import better_auto_moderator.config as config
from better_auto_moderator.reddit import subreddit, reddit
from better_auto_moderator.moderators.comment_moderator import CommentModerator
from better_auto_moderator.moderators.modqueue_moderator import ModqueueModerator

#config.push_rules()

rules_by_type = {}
rules = config.get_bam_rules()

for rule in rules:
    if rule.type not in rules_by_type:
        rules_by_type[rule.type] = []

    rules_by_type[rule.type].append(rule)

if "modmail" in rules_by_type:
    rules = sorted(rules_by_type['modmail'], key=lambda rule: rule.priority)
    print("Listening for modmail conversations")
    for message in subreddit.mod.stream.modmail_conversations():
        for rule in rules:
            if rule.process(message):
                break

if "comment" in rules_by_type:
    rules = sorted(rules_by_type['comment'], key=lambda rule: rule.priority)
    print("Listening for comment submissions")
    for item in subreddit.stream.comments():
        moderator = CommentModerator(item)
        for rule in rules:
            if moderator.moderate(rule):
                break
    #submission = reddit.submission("hdr2ap")
    #print("evaluating", submission)
    #print(CommentModerator(submission).moderate(rules[0]))

if "modqueue" in rules_by_type:
    rules = sorted(rules_by_type['modqueue'], key=lambda rule: rule.priority)
    print("Listening for modqueue conversations")
    for item in subreddit.mod.stream.modqueue():
        moderator = ModqueueModerator(item)
        for rule in rules:
            if moderator.moderate(rule):
                break
