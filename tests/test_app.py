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
        'classes': [{'qid': 'Q81163', 'label': 'polymer'}],
        'monomers': [{'qid': 'Q1055852', 'label': '2,6-xylenol'}],
        'identifiers': {'cas': ['25134-01-4'], 'chebi': [],
                        'pubchem_cid': ['6378'],
                        'pubchem_sid': ['135283456']},
        'wikipedia': {
            'en': 'https://en.wikipedia.org/wiki/Poly(p-phenylene_oxide)',
            'nl': 'https://nl.wikipedia.org/wiki/Polyfenyleenoxide'},
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
        'cxsmiles': [], 'classes': [], 'monomers': [],
        'identifiers': {'cas': [], 'chebi': [], 'pubchem_cid': [],
                        'pubchem_sid': []},
        'wikipedia': {}, 'properties': [],
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
        self.assertIn('hreflang="en" title="English Wikipedia">GB</a>', page)
        self.assertIn('hreflang="nl" title="Dutch Wikipedia">NL</a>', page)

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
