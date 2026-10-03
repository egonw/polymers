"""Writes cxsmiles-comparison.html: for every polymer with a chemical structure
image (P117), that image next to the CDK Depict drawing of its CXSMILES
(P10718), so the two can be compared by eye.

CXSMILES that are proposed but not yet in Wikidata can be put in polymers.qs,
as QuickStatements (`Qxxx<TAB>P10718<TAB>"cxsmiles"`); they are shown too.
Run it with `make curate`.
"""

import html

import curation
from curation import log

OUTPUT = curation.ROOT / 'cxsmiles-comparison.html'
PROPOSALS = curation.ROOT / 'polymers.qs'

STYLE = '''
.pair { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1rem; }
@media (max-width:40rem) { .pair { grid-template-columns:minmax(0,1fr); } }
figure { margin:0 0 .75rem; }
figure img { display:block; width:100%; max-height:18rem; object-fit:contain; padding:.5rem;
             background:#fff; border:1px solid var(--border); border-radius:6px; }
figcaption { font-size:.8rem; overflow-wrap:anywhere; }
.none { padding:2rem 1rem; text-align:center; color:var(--muted);
        border:1px dashed var(--border); border-radius:6px; }
nav a { margin-right:1rem; }
'''

SECTIONS = [
    ('proposed', 'Proposed CXSMILES',
     'CXSMILES from polymers.qs that are not yet in Wikidata.'),
    ('missing', 'No CXSMILES yet',
     'Polymers with a chemical structure image but without a CXSMILES.'),
    ('present', 'CXSMILES in Wikidata',
     'Check that the drawing of the CXSMILES matches the image.'),
]


def read_proposals():
    """The CXSMILES in polymers.qs, by QID."""
    proposals = {}
    if PROPOSALS.exists():
        for line in PROPOSALS.read_text(encoding='utf-8').splitlines():
            fields = line.split('\t')
            if len(fields) >= 3 and fields[1] == 'P10718':
                proposals.setdefault(fields[0], []).append(fields[2].strip('"'))
    return proposals


def card(polymer, structures, smiles, kind):
    originals = ''.join(
        f'<figure><img src="{curation.commons_thumb(name, 500)}" '
        f'alt="Commons image {html.escape(name)}"><figcaption>'
        f'<a href="{curation.commons_page(name)}">{html.escape(name)}</a>'
        f'</figcaption></figure>' for name in structures)
    if smiles:
        drawings = ''.join(
            f'<figure><img src="{curation.depiction(cx)}" alt="CDK Depict '
            f'drawing"><figcaption><code>{html.escape(cx)}</code>'
            f'</figcaption></figure>' for cx in smiles)
    else:
        drawings = '<p class="none">No CXSMILES in Wikidata</p>'
    source = 'polymers.qs' if kind == 'proposed' else 'Wikidata'
    return f'''
  <section class="card">
    <h2><a href="https://www.wikidata.org/wiki/{polymer['qid']}">{html.escape(polymer['label'])}</a> <span class="muted">{polymer['qid']}</span></h2>
    <div class="pair">
      <div><p class="label">Chemical structure (P117)</p>{originals}</div>
      <div><p class="label">CXSMILES ({source}), by CDK Depict</p>{drawings}</div>
    </div>
  </section>'''


def main():
    polymers = curation.load_polymers()
    images = curation.linked_images(polymers)
    proposals = read_proposals()
    groups = {key: [] for key, _, _ in SECTIONS}
    for polymer in polymers:
        structures = images.get(polymer['qid'], {}).get('P117')
        if not structures:
            continue
        log(polymer['qid'], polymer['label'])
        if polymer['qid'] in proposals and not polymer['cxsmiles']:
            kind, smiles = 'proposed', proposals[polymer['qid']]
        elif polymer['cxsmiles']:
            kind, smiles = 'present', polymer['cxsmiles']
        else:
            kind, smiles = 'missing', []
        groups[kind].append(card(polymer, structures, smiles, kind))

    shown = [(key, title, text) for key, title, text in SECTIONS if groups[key]]
    nav = '<nav>' + ''.join(
        f'<a href="#{key}">{title} ({len(groups[key])})</a>'
        for key, title, _ in shown) + '</nav>'
    body = nav + ''.join(
        f'<h2 id="{key}" class="label">{title}</h2><p class="muted">{text}</p>'
        + ''.join(groups[key]) for key, title, text in shown)
    total = sum(len(cards) for cards in groups.values())
    intro = (f'The {total} polymers with a chemical structure image (P117) in '
             'Wikidata. Left: the image on Wikimedia Commons; right: the '
             'CXSMILES (P10718) drawn by CDK Depict.')
    curation.write(OUTPUT, curation.page(
        'CXSMILES Comparison', 'CXSMILES comparison', intro, body, STYLE))


if __name__ == '__main__':
    main()
