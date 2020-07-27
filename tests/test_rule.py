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

    def test_sort_rules(self):
        first = Rule.sort_rules([
            Rule({
                'name': 'two',
                'priority': 2
            }),
            Rule({
                'name': 'three',
                'priority': 1
            }),
            Rule({
                'name': 'one',
                'priority': 3
            })
        ])
        self.assertEqual(first[0].config['name'], 'one')
        self.assertEqual(first[1].config['name'], 'two')
        self.assertEqual(first[2].config['name'], 'three')

        second = Rule.sort_rules([
            Rule({
                'name': 'four',
                'priority': 2
            }),
            Rule({
                'name': 'two',
                'priority': 1,
                'action': 'remove'
            }),
            Rule({
                'name': 'three',
                'priority': 5
            }),
            Rule({
                'name': 'one',
                'priority': 3,
                'action': 'remove'
            })
        ])
        self.assertEqual(second[0].config['name'], 'one')
        self.assertEqual(second[1].config['name'], 'two')
        self.assertEqual(second[2].config['name'], 'three')
        self.assertEqual(second[3].config['name'], 'four')
