import json
import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.views import depict, quantity

POLYMERS = [
    {
        'qid': 'Q146206',
        'label': 'poly(p-phenylene oxide)',
        'description': 'polymer',
        'cxsmiles': ['[*]CC[*] |Sg:n:1,2::ht|'],
        'photos': ['PPO sample (1).jpg'],
        'classes': [{'qid': 'Q81163', 'label': 'polymer'}],
        'monomers': [{'qid': 'Q1055852', 'label': '2,6-xylenol'}],
        'identifiers': {'cas': ['25134-01-4'], 'chebi': [],
                        'pubchem_cid': ['6378'],
                        'pubchem_sid': ['135283456']},
        'wikipedia': {
            'en': 'https://en.wikipedia.org/wiki/Poly(p-phenylene_oxide)',
            'nl': 'https://nl.wikipedia.org/wiki/Polyfenyleenoxide'},
        'members': [],
        'properties': [{
            'property': 'P2054', 'label': 'density', 'value': '1.06',
            'lower': '1.05', 'upper': '1.07',
            'unit': {'qid': 'Q13147228', 'label': 'gram per cubic centimetre'},
            'qualifiers': [{'property': 'P2076', 'label': 'temperature',
                            'value': '20.0', 'valueLabel': None,
                            'unit': {'qid': 'Q25267',
                                     'label': 'degree Celsius'}}],
            'references': [{'source': 'Q20887890', 'label': 'CRC Handbook',
                            'doi': '10.1201/B17118', 'url': None}],
        }],
    },
    {
        'qid': 'Q62246', 'label': 'polycarbonate', 'description': None,
        'cxsmiles': [], 'photos': [], 'classes': [], 'monomers': [],
        'identifiers': {'cas': [], 'chebi': [], 'pubchem_cid': [],
                        'pubchem_sid': []},
        'wikipedia': {}, 'properties': [],
        'members': [
            {'qid': 'Q146206', 'label': 'poly(p-phenylene oxide)',
             'cxsmiles': [], 'photos': [], 'wikipedia': {}},
            {'qid': 'Q110254858', 'label': 'poly(bisphenol A carbonate)',
             'cxsmiles': ['[*]CC[*] |Sg:n:1,2::ht|'],
             'photos': ['Lexan sheet.jpg'],
             'wikipedia': {'de': 'https://de.wikipedia.org/wiki/PC'}},
        ],
    },
]


class AppTest(unittest.TestCase):

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / 'polymers.json'
        path.write_text(json.dumps(POLYMERS))
        self.client = create_app(path).test_client()

    def test_index_lists_polymers(self):
        page = self.client.get('/').get_data(as_text=True)
        self.assertIn('poly(p-phenylene oxide)', page)
        self.assertIn('polycarbonate', page)
        self.assertIn('href="/Q146206/"', page)
        self.assertIn('cdkdepict.toolforge.org', page)
        self.assertIn('No CXSMILES in Wikidata', page)
        self.assertIn('href="https://doi.org/10.26434/chemrxiv-2025-53n0w"', page)
        self.assertIn('href="https://commons.wikimedia.org/wiki/File:PPO_sample_%281%29.jpg"', page)
        self.assertIn('src="https://commons.wikimedia.org/wiki/Special:FilePath/PPO%20sample%20%281%29.jpg?width=150"', page)
        self.assertIn('hreflang="en" title="English Wikipedia">EN</a>', page)
        self.assertIn('hreflang="nl" title="Dutch Wikipedia">NL</a>', page)
        self.assertIn('href="/Q62246/#members" title="2 polymers in this class">2</a>', page)
        # Only classes of polymers get a count.
        self.assertEqual(page.count('polymers in this class'), 1)

    def test_polymer_page(self):
        response = self.client.get('/Q146206/')
        self.assertEqual(response.status_code, 200)
        page = response.get_data(as_text=True)
        self.assertIn('density', page)
        self.assertIn('1.06 ± 0.01', page)
        self.assertIn('temperature:', page)
        self.assertIn('https://doi.org/10.1201/B17118', page)
        self.assertIn('2,6-xylenol', page)
        self.assertIn('hreflang="nl">Dutch</a>', page)
        self.assertIn('https://pubchem.ncbi.nlm.nih.gov/compound/6378', page)
        self.assertIn('https://pubchem.ncbi.nlm.nih.gov/substance/135283456',
                      page)

    def test_polymer_without_properties(self):
        page = self.client.get('/Q62246/').get_data(as_text=True)
        self.assertIn('no physicochemical properties', page)

    def test_class_lists_members(self):
        page = self.client.get('/Q62246/').get_data(as_text=True)
        self.assertIn('Polymers in this class', page)
        # A member with a page here links to it, the others to Wikidata.
        self.assertIn('href="/Q146206/"', page)
        self.assertIn('href="https://www.wikidata.org/wiki/Q110254858"', page)
        self.assertIn('title="German Wikipedia">DE</a>', page)
        self.assertIn('href="https://commons.wikimedia.org/wiki/File:Lexan_sheet.jpg"', page)

    def test_polymer_without_members(self):
        page = self.client.get('/Q146206/').get_data(as_text=True)
        self.assertNotIn('Polymers in this class', page)

    def test_unknown_polymer(self):
        self.assertEqual(self.client.get('/Q1/').status_code, 404)


class FilterTest(unittest.TestCase):

    def test_depict_encodes_cxsmiles(self):
        url = depict('[*]CC[*] |Sg:n:1,2::ht|')
        self.assertIn('smi=%5B%2A%5DCC%5B%2A%5D%20%7CSg%3An%3A1%2C2%3A%3Aht%7C',
                      url)

    def test_quantity(self):
        self.assertEqual(quantity({'value': '1250.0'}), '1250')
        self.assertEqual(
            quantity({'value': '120.0', 'lower': '110.0', 'upper': '130.0'}),
            '120 ± 10')
        self.assertEqual(
            quantity({'value': '1.2', 'lower': '1.1', 'upper': '1.4'}),
            '1.2 (1.1 to 1.4)')
        self.assertEqual(
            quantity({'value': '1.2', 'lower': '1.2', 'upper': '1.2'}), '1.2')


if __name__ == '__main__':
    unittest.main()
