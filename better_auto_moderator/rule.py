import yaml

class Rule:
    requires_bam = False

    def __init__(self, config):
        self.raw = config
        self.parse(self.raw)

    def to_reddit(self):
        config = dict(self.config)
        config['priority'] = self.priority
        config['type'] = self.type

        return yaml.dump(config, Dumper=yaml.Dumper)

    def parse(self, config):
        self.priority = 0
        self.type = 'any'
        self.config = { }

        for key in config.keys():
            parser_name = "parse_%s" % key
            if hasattr(self, parser_name):
                getattr(self, parser_name)(config.get(key))
            else:
                self.config[key] = config.get(key)

        if self.requires_bam and self.config.hasattr('standard'):
            raise Exception('Standard check defined for a BAM rule. Standards are not supported by BAM.')

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

    def parse_bam(self, value):
        self.requires_bam = value
