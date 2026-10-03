"""Updates _data/polymers.json with the polymers in Wikidata.

Runs the SPARQL queries in sparql/ against the QLever instance of Wikidata and
writes one JSON record per polymer, sorted by QID. Run it with `make update`.
"""

import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
SPARQL_DIR = ROOT / 'sparql'
OUTPUT = ROOT / '_data' / 'polymers.json'

ENDPOINT = 'https://qlever.dev/api/wikidata'
USER_AGENT = 'PolymersWebsite/1.0 (Wikidata polymer pages; python-requests)'
TIMEOUT = 300

ENTITY = 'http://www.wikidata.org/entity/'
GENID = '/.well-known/genid/'
SOMEVALUE = 'somevalue'
# The unit of dimensionless quantities, such as the refractive index.
NO_UNIT = 'Q199'
# Statements per references and qualifiers query, to keep the queries small.
CHUNK = 200
# Waits, in seconds, before trying again when QLever is busy (429, 503).
RETRY_WAITS = (10, 30, 60, 120)


def run_query(query):
    """Runs a query and gives its rows as dicts of plain values."""
    for wait in RETRY_WAITS + (None,):
        response = requests.post(
            ENDPOINT, data={'query': query}, timeout=TIMEOUT,
            headers={'Accept': 'application/sparql-results+json',
                     'User-Agent': USER_AGENT})
        # QLever also answers 429 when a query times out; trying again
        # does not help then.
        busy = (response.status_code in (429, 503)
                and 'timed out' not in response.text)
        if not busy or wait is None:
            break
        retry_after = response.headers.get('Retry-After', '')
        if retry_after.isdigit():
            wait = int(retry_after)
        print(f'  QLever answered {response.status_code}, '
              f'trying again in {wait} s', file=sys.stderr)
        time.sleep(wait)
    try:
        answer = response.json()
    except ValueError:
        response.raise_for_status()
        raise
    if 'results' not in answer:
        raise RuntimeError(f'QLever answered {response.status_code}: '
                           f"{answer.get('exception', 'no results')}")
    rows = []
    for binding in answer['results']['bindings']:
        row = {name: short(value['value']) for name, value in binding.items()}
        # Use the "mul" (all languages) label when there is no English one.
        for name in [name for name in row if name.endswith('Mul')]:
            row.setdefault(name[:-3], row.pop(name))
        rows.append(row)
    return rows


def short(value):
    """Turns entity IRIs into QIDs and PIDs, and unknown values ("somevalue",
    blank nodes that QLever gives as genid IRIs) into SOMEVALUE; leaves other
    values as they are."""
    if GENID in value:
        return SOMEVALUE
    if value.startswith(ENTITY) and '/' not in value[len(ENTITY):]:
        return value[len(ENTITY):]
    return value


def read_query(name):
    return (SPARQL_DIR / name).read_text()


def qid_number(qid):
    return int(qid[1:])


def number(value):
    """Wikidata amounts as written, without a leading plus sign."""
    return value[1:] if value.startswith('+') else value


def add_unique(items, item):
    if item not in items:
        items.append(item)


def collect_polymers(rows):
    polymers = {}
    for row in rows:
        qid = row['polymer']
        polymer = polymers.setdefault(qid, {
            'qid': qid,
            'label': row.get('polymerLabel', qid),
            'description': row.get('polymerDescription'),
            'cxsmiles': [],
            'classes': [],
            'monomers': [],
            'identifiers': {'cas': [], 'chebi': [], 'pubchem': []},
            'wikipedia': row.get('article'),
            'properties': [],
        })
        if 'cxsmiles' in row:
            add_unique(polymer['cxsmiles'], row['cxsmiles'])
        if 'class' in row:
            add_unique(polymer['classes'],
                       {'qid': row['class'],
                        'label': row.get('classLabel', row['class'])})
        if 'monomer' in row:
            add_unique(polymer['monomers'],
                       {'qid': row['monomer'],
                        'label': row.get('monomerLabel', row['monomer'])})
        for key in ('cas', 'chebi', 'pubchem'):
            if key in row:
                add_unique(polymer['identifiers'][key], row[key])
    return polymers


def collect_properties(rows):
    """Gives the property statements, keyed by statement IRI."""
    statements = {}
    for row in rows:
        unit = row['unit']
        statements[row['statement']] = {
            'polymer': row['polymer'],
            'property': row['property'],
            'label': row.get('propertyLabel', row['property']),
            'value': number(row['amount']),
            'lower': number(row['lower']) if 'lower' in row else None,
            'upper': number(row['upper']) if 'upper' in row else None,
            'unit': None if unit == NO_UNIT else {
                'qid': unit, 'label': row.get('unitLabel', unit)},
            'qualifiers': [],
            'references': [],
        }
    return statements


def chunks(items, size):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def run_for_statements(name, statements):
    """Runs a query with {{statements}} for all statements, in chunks."""
    template = read_query(name)
    rows = []
    for chunk in chunks(sorted(statements), CHUNK):
        values = ' '.join(f'<{statement}>' for statement in chunk)
        rows.extend(run_query(template.replace('{{statements}}', values)))
    return rows


def add_references(statements, rows):
    for row in rows:
        reference = {
            'source': row.get('source'),
            'label': row.get('sourceLabel', row.get('source')),
            'doi': row.get('doi'),
            'url': row.get('url'),
        }
        if any(reference.values()):
            add_unique(statements[row['statement']]['references'], reference)


def add_qualifiers(statements, rows):
    for row in rows:
        unit = row.get('unit')
        value = row['value']
        add_unique(statements[row['statement']]['qualifiers'], {
            'property': row['qualifier'],
            'label': row.get('qualifierLabel', row['qualifier']),
            'value': number(value) if unit else value,
            'valueLabel': ('unknown value' if value == SOMEVALUE
                           else row.get('valueLabel')),
            'unit': None if unit in (None, NO_UNIT) else {
                'qid': unit, 'label': row.get('unitLabel', unit)},
        })


def sort_key(statement):
    try:
        value = float(statement['value'])
    except ValueError:
        value = 0.0
    return (statement['label'].lower(), value, statement['value'])


def build():
    print('Polymers ...', file=sys.stderr)
    polymers = collect_polymers(run_query(read_query('polymers.rq')))
    print('Properties ...', file=sys.stderr)
    statements = collect_properties(run_query(read_query('properties.rq')))
    print('References ...', file=sys.stderr)
    add_references(statements, run_for_statements('references.rq', statements))
    print('Qualifiers ...', file=sys.stderr)
    add_qualifiers(statements, run_for_statements('qualifiers.rq', statements))

    for statement in statements.values():
        polymer = polymers.get(statement.pop('polymer'))
        if polymer:
            polymer['properties'].append(statement)
    for polymer in polymers.values():
        polymer['cxsmiles'].sort()
        polymer['classes'].sort(key=lambda item: qid_number(item['qid']))
        polymer['monomers'].sort(key=lambda item: qid_number(item['qid']))
        for values in polymer['identifiers'].values():
            values.sort()
        polymer['properties'].sort(key=sort_key)
        for statement in polymer['properties']:
            statement['qualifiers'].sort(key=lambda q: (q['label'], q['value']))
            statement['references'].sort(
                key=lambda r: (r['label'] or '', r['doi'] or '', r['url'] or ''))
    return sorted(polymers.values(), key=lambda p: qid_number(p['qid']))


def main():
    polymers = build()
    OUTPUT.parent.mkdir(exist_ok=True)
    with OUTPUT.open('w', encoding='utf-8') as file:
        json.dump(polymers, file, indent=2, ensure_ascii=False)
        file.write('\n')
    with_structure = sum(1 for polymer in polymers if polymer['cxsmiles'])
    print(f'Wrote {len(polymers)} polymers ({with_structure} with a CXSMILES) '
          f'to {OUTPUT.relative_to(ROOT)}', file=sys.stderr)


if __name__ == '__main__':
    main()
