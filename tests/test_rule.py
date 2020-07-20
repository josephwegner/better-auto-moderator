import unittest
from mock import patch, MagicMock
from better_auto_moderator.rule import Rule

class ModeratorTestCase(unittest.TestCase):
    def test_standard(self):
        with self.assertRaises(Exception, msg='Standard check defined for a BAM rule. Standards are not supported by BAM.'):
            Rule({
                'bam': True,
                'standard': 'image hosting sites'
            })

        # This will error if standard is disallow for non-BAM rules
        Rule({
            'standard': 'image hosting sites'
        })
