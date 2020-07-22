import yaml
import os
from better_auto_moderator.rule import Rule
import better_auto_moderator.reddit

rules = []

# Read the rules out of /etc/automod.yaml
def get_rules():
    global rules
    rules = []
    with open(os.path.join(os.getcwd(), 'etc', 'automod.yaml'), 'r') as file:
        full_text = file.read()
        raw_rules = [rule.strip() for rule in full_text.split('---')]
        for raw in raw_rules:
            if len(raw) == 0:
                continue
                
            rules.append(Rule(yaml.load(raw, Loader=yaml.Loader)))

        return rules

def get_bam_rules():
    if len(rules) == 0:
        get_rules()

    bam_rules = []
    for rule in rules:
        if rule.requires_bam:
            bam_rules.append(rule)
    return bam_rules

def get_automod_rules():
    if len(rules) == 0:
        get_rules()

    automod_rules = []
    for rule in rules:
        if not rule.requires_bam:
            automod_rules.append(rule)
    return automod_rules

def push_rules():
    rules_for_reddit = []
    for rule in get_automod_rules():
        rules_for_reddit.append(rule.to_reddit())

    # Little bit of formatting here to make it more readable
    full_yaml = "\n---\n\n".join(rules_for_reddit)
    reddit.update_automod_config(full_yaml)
