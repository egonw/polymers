import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))

import update_polymers as update  # noqa: E402


class UpdateTest(unittest.TestCase):

    def test_short(self):
        self.assertEqual(update.short('http://www.wikidata.org/entity/Q42'),
                         'Q42')
        statement = 'http://www.wikidata.org/entity/statement/Q42-abc'
        self.assertEqual(update.short(statement), statement)
        self.assertEqual(
            update.short('http://www.wikidata.org/.well-known/genid/123'),
            update.SOMEVALUE)

    def test_collect_polymers_merges_rows(self):
        rows = [
            {'polymer': 'Q146206', 'polymerLabel': 'PPO', 'cxsmiles': 'C',
             'class': 'Q81163', 'classLabel': 'polymer', 'cas': '1'},
            {'polymer': 'Q146206', 'polymerLabel': 'PPO', 'cxsmiles': 'C',
             'class': 'Q7226747', 'classLabel': 'polyphenyl ether',
             'cas': '1'},
        ]
        polymer = update.collect_polymers(rows)['Q146206']
        self.assertEqual(polymer['cxsmiles'], ['C'])
        self.assertEqual(len(polymer['classes']), 2)
        self.assertEqual(polymer['identifiers']['cas'], ['1'])

    def test_dimensionless_unit(self):
        statements = update.collect_properties([{
            'polymer': 'Q62246', 'property': 'P1109',
            'propertyLabel': 'refractive index', 'statement': 's1',
            'amount': '+1.585', 'unit': update.NO_UNIT}])
        self.assertIsNone(statements['s1']['unit'])
        self.assertEqual(statements['s1']['value'], '1.585')


if __name__ == '__main__':
    unittest.main()
