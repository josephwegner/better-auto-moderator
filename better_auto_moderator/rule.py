import yaml
from operator import itemgetter

class Rule:
    # We'll flip this to True whenever a rule uses options that are not supported
    # by Automoderator. This flag is used for BAM to know which rules it should implement
    requires_bam = False

    def __init__(self, config):
        self.raw = config
        self.config = {}
        self.type = 'any'
        self.priority = 0
        self.parse(self.raw)

    @staticmethod
    def sort_rules(rules):
        return sorted(rules, key=lambda rule: (-int(rule.is_priority()), -rule.priority))

    # Output the rules in a YAML format that Automoderator will understand
    def to_reddit(self):
        config = dict(self.config)
        config['priority'] = self.priority
        config['type'] = self.type

        return yaml.dump(config, Dumper=yaml.Dumper)

    def is_priority(self):
        if 'action' in self.config and self.config['action'] in ['remove', 'spam', 'filter']:
            return True
        return False

    def parse(self, config):
        for key in config.keys():
            # This class has a bunch of parse_* methods that will be used to parse the rule
            # For instance, if a rule has `type: submission`, that will be parsed by
            # the `parse_type` function.
            # If a parser doesn't exist, just add the line straight into the config
            parser_name = "parse_%s" % key
            if hasattr(self, parser_name):
                getattr(self, parser_name)(config.get(key))
            else:
                self.config[key] = config.get(key)

        # standards are propreitary lists owned by Reddit. We don't have access, so we BAM can't implement them
        if self.requires_bam and 'standard' in self.config:
            raise Exception('Standard check defined for a BAM rule. Standards are not supported by BAM.')

        if self.requires_bam and self.config.get('action') == 'filter':
            raise Exception('Filter actions cannot be run by BAM.')

    def parse_type(self, type):
        self.type = type

        if type in ['modmail', 'report']:
            self.requires_bam = True

    def parse_ignore_reports(self, val):
        if val:
            self.config['ignore_reports'] = True
            self.requires_bam = True

    def parse_priority(self, priority):
        self.priority = priority

    # `bam: true` can be set in a rule to force it to be run by BAM. This is good for testing.
    def parse_bam(self, value):
        self.requires_bam = value
