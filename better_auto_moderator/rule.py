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

        self.set_standards()

        if self.requires_bam and self.config.get('action') == 'filter':
            raise Exception('Filter actions cannot be run by BAM.')

    def set_standards(self):
        if 'standard' in self.config:
            standard = self.config['standard']

            if standard == 'image hosting sites':
                self.config['domain'] = ['500px.com', 'abload.de', 'anony.ws', 'deviantart.com', 'deviantart.net', 'fav.me', 'fbcdn.net', 'flickr.com', 'forgifs.com', 'giphy.com', 'gfycat.com', 'gifs.com', 'gifsoup.com', 'gyazo.com', 'imageshack.us', 'imgclean.com', 'imgur.com', 'instagr.am', 'instagram.com', 'i.reddituploads.com', 'mediacru.sh', 'media.tumblr.com', 'min.us', 'minus.com', 'myimghost.com', 'photobucket.com', 'picsarus.com', 'postimg.org', 'puu.sh', 'i.redd.it', 'sli.mg', 'staticflickr.com', 'tinypic.com', 'twitpic.com', 'ibb.co']

            elif standard == 'direct image links':
                self.config['url (regex)'] = '\\.(jpe?g|png|gifv?)(\\?\\S*)?$'

            elif standard == 'streaming sites':
                self.config['domain'] = ['twitch.tv', 'livestream.com', 'azubu.tv', 'hitbox.tv', 'ustream.tv']
                self.config['~domain'] = content.azubu.tv

            elif standard == 'video hosting sites':
                self.config['domain'] = ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com', 'liveleak.com', 'mediacru.sh', 'worldstarhiphop.com', 'gfycat.com', 'vid.me']

            elif standard == 'meme generator sites':
                self.config['domain'] = ['9gag.com', 'cheezburger.com', 'chzbgr.com', 'diylol.com', 'dropmeme.com', 'generatememes.com', 'ifunny.co', 'imgflip.com', 'ismeme.com', 'livememe.com', 'makeameme.org', 'meme-generator.org', 'memecaptain.com', 'memecenter.com', 'memecloud.net', 'memecreator.org', 'memecrunch.com', 'memedad.com', 'memegen.com', 'memegenerator.co', 'memegenerator.net', 'mememaker.net', 'memesly.com', 'memesnap.com', 'minimemes.net', 'onsizzle.com', 'pressit.co', 'qkme.me', 'quickmeme.com', 'ratemymeme.com', 'sizzle.af', 'troll.me', 'weknowmemes.com', 'winmeme.com', 'wuzu.se']

            elif standard == 'facebook links':
                self.config['url+body (regex)'] = ["facebook\\.com", "fbcdn\\.net", "fb\\.com", "fb\\.me", "fbcdn-s?photos-.*?\\.akamaihd\\.net"]

            elif standard == 'amazon affiliate links':
                self.config['url+body (regex)'] = "(amazon|amzn)\\.(com|co\\.uk|ca)\\S+?tag="

            elif standard == 'crowdfunding sites':
                self.config['domain'] = ['crowdrise.com', 'kickstarter.com', 'kck.st', 'giveforward.com', 'gogetfunding.com', 'indiegogo.com', 'igg.me', 'generosity.com', 'gofundme.com', 'patreon.com', 'prefundia.com', 'razoo.com', 'totalgiving.co.uk', 'youcaring.com', 'youcaring.net', 'youcaring.org', 'petcaring.com', 'walacea.com']
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

    def parse_log(self, log):
        self.config['log'] = log
        self.requires_bam = True

    # `bam: true` can be set in a rule to force it to be run by BAM. This is good for testing.
    def parse_bam(self, value):
        self.requires_bam = value
