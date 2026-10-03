"""Writes wikipedia-photos.html: the photos on Wikimedia Commons that are used
on the Wikipedia articles of the polymers but that Wikidata does not link
(as image, P18, or chemical structure, P117), each with QuickStatements that
add it as image. Run it with `make curate`.
"""

import html
from collections import defaultdict
from urllib.parse import quote, unquote

import curation
import update_polymers as update
from curation import log

OUTPUT = curation.ROOT / 'wikipedia-photos.html'

# The Wikipedias, with their code on the page and their item, which is the
# reference of the statements (imported from Wikimedia project, P143).
WIKIPEDIAS = {
    'en': ('EN', 'English', 'Q328'),
    'nl': ('NL', 'Dutch', 'Q10000'),
    'de': ('DE', 'German', 'Q48183'),
    'fr': ('FR', 'French', 'Q8447'),
    'it': ('IT', 'Italian', 'Q11920'),
}
ORDER = list(WIKIPEDIAS)
TIERS = ['Lead image of a Wikipedia article',
         'Used on two or more Wikipedias',
         'Used on one Wikipedia']
QUICKSTATEMENTS = 'https://quickstatements.toolforge.org/#/v1='

STYLE = '''
body { padding-bottom:12rem; }
main { max-width:60rem; }
.has, .none { margin-left:.4rem; font-size:.75rem; font-weight:500; }
.has { color:var(--muted); } .none { color:var(--flag); }
.row { display:grid; grid-template-columns:120px minmax(0,1fr); gap:1rem; padding:.75rem 0;
       border-top:1px solid var(--border); }
.thumb img { display:block; width:120px; height:120px; object-fit:cover; background:#fff;
             border:1px solid var(--border); border-radius:6px; }
.lead .thumb img { border:2px solid var(--lead); }
.file { font-weight:500; overflow-wrap:anywhere; }
.wikis { margin:.2rem 0 .4rem; font-size:.85rem; color:var(--muted); }
.badge { display:inline-block; margin-left:.25rem; padding:0 .3rem; border:1px solid var(--border);
         border-radius:4px; font-size:.7rem; font-weight:600; text-decoration:none; color:var(--muted); }
.badge:hover { color:var(--accent); border-color:var(--accent); }
.actions { display:flex; flex-wrap:wrap; align-items:center; gap:.4rem 1rem; margin-top:.4rem;
           font-size:.85rem; }
button { font:inherit; padding:.15rem .6rem; color:var(--text); background:var(--card);
         border:1px solid var(--border); border-radius:4px; cursor:pointer; }
button:hover { border-color:var(--accent); color:var(--accent); }
.batch { position:fixed; left:0; right:0; bottom:0; padding:.75rem 1rem; background:var(--card);
         border-top:1px solid var(--border); }
.batch div { max-width:60rem; margin:0 auto; }
.batch textarea { width:100%; height:5rem; margin-top:.4rem; color:var(--text); background:var(--code);
                  font:.78rem/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
                  border:1px solid var(--border); border-radius:4px; }
@media (max-width:34rem) { .row { grid-template-columns:80px minmax(0,1fr); }
                           .thumb img { width:80px; height:80px; } }
'''

SCRIPT = '''
<div class="batch"><div>
  <strong>Batch</strong> <span class="muted" id="count">0 statements</span>
  <button type="button" id="copy-batch">Copy</button>
  <a id="open-batch" href="#" target="_blank" rel="noopener">Open in QuickStatements</a>
  <textarea id="batch" readonly placeholder="Tick “add to batch” on the rows to collect their QuickStatements here."></textarea>
</div></div>
<script>
function copy(text, button) {
  navigator.clipboard.writeText(text).then(function () {
    var label = button.textContent; button.textContent = 'Copied';
    setTimeout(function () { button.textContent = label; }, 1200);
  });
}
function v1(lines) {
  return 'QUICKSTATEMENTS' + encodeURIComponent(
    lines.map(function (l) { return l.split('\\t').join('|'); }).join('||'));
}
function update() {
  var lines = Array.prototype.map.call(document.querySelectorAll('.pick:checked'),
    function (box) { return box.closest('.row').dataset.qs; });
  document.getElementById('batch').value = lines.join('\\n');
  document.getElementById('count').textContent =
    lines.length + (lines.length === 1 ? ' statement' : ' statements');
  document.getElementById('open-batch').href = lines.length ? v1(lines) : '#';
}
document.addEventListener('click', function (e) {
  if (e.target.matches('.row .copy')) copy(e.target.closest('.row').dataset.qs, e.target);
  if (e.target.id === 'copy-batch') copy(document.getElementById('batch').value, e.target);
});
document.addEventListener('change', function (e) { if (e.target.matches('.pick')) update(); });
update();
</script>'''.replace('QUICKSTATEMENTS', QUICKSTATEMENTS)


def article_images(polymers):
    """The images on the Wikipedia articles of the polymers, as {qid: {file:
    {languages}}}, and the lead images of the articles, as {qid: {files}}."""
    titles = defaultdict(dict)
    for polymer in polymers:
        for language, url in polymer['wikipedia'].items():
            title = unquote(url.split('/wiki/', 1)[1]).replace('_', ' ')
            titles[language][title] = polymer['qid']
    used = defaultdict(lambda: defaultdict(set))
    lead = defaultdict(set)
    for language, articles in titles.items():
        api = f'https://{language}.wikipedia.org/w/api.php'
        for chunk in update.chunks(sorted(articles), 50):
            params = {'action': 'query', 'format': 'json', 'formatversion': 2,
                      'titles': '|'.join(chunk), 'prop': 'images|pageimages',
                      'imlimit': 'max', 'piprop': 'name', 'redirects': 1}
            asked = {title: title for title in chunk}
            while True:
                answer = curation.request('POST', api, data=params).json()
                query = answer.get('query', {})
                for step in query.get('normalized', []) + query.get('redirects', []):
                    asked[step['to']] = asked.get(step['from'], step['from'])
                for page in query.get('pages', []):
                    qid = articles.get(asked.get(page['title'], page['title']))
                    if not qid:
                        continue
                    for image in page.get('images', []):
                        used[qid][image['title'].split(':', 1)[1]].add(language)
                    if page.get('pageimage'):
                        lead[qid].add(page['pageimage'].replace('_', ' '))
                if 'continue' not in answer:
                    break
                params.update(answer['continue'])
        log(f'{language}: {len(articles)} articles')
    return used, lead


def statement(qid, name, languages):
    source = WIKIPEDIAS[languages[0]][2]
    return f'{qid}\tP18\t"{name}"\tS143\t{source}'


def row(polymer, name, languages, lead):
    commons = curation.commons_page(name)
    wikis = ''.join(
        f'<a class="badge" href="{html.escape(polymer["wikipedia"][language])}" '
        f'hreflang="{language}" title="{WIKIPEDIAS[language][1]} Wikipedia '
        f'article">{WIKIPEDIAS[language][0]}</a>' for language in languages)
    if '"' in name:
        # QuickStatements cannot write a double quote in a string value.
        data = ''
        actions = ('<p class="muted">No QuickStatements: the file name has a '
                   'double quote, which QuickStatements cannot write. Add it '
                   'on Wikidata by hand.</p>')
    else:
        line = statement(polymer['qid'], name, languages)
        link = QUICKSTATEMENTS + quote(line.replace('\t', '|'), safe='')
        data = f' data-qs="{html.escape(line)}"'
        actions = f'''<code>{html.escape(line)}</code>
          <div class="actions">
            <button type="button" class="copy">Copy</button>
            <a href="{link}" target="_blank" rel="noopener">Open in QuickStatements</a>
            <label><input type="checkbox" class="pick"> add to batch</label>
          </div>'''
    return f'''
      <div class="row{' lead' if lead else ''}"{data}>
        <a class="thumb" href="{commons}"><img src="{curation.commons_thumb(name, 240)}" alt="{html.escape(name)}" loading="lazy"></a>
        <div class="info">
          <a class="file" href="{commons}">{html.escape(name)}</a>
          <div class="wikis">Used on {wikis}</div>
          {actions}
        </div>
      </div>'''


def main():
    polymers = curation.load_polymers()
    linked = curation.linked_images(polymers)
    used, lead = article_images(polymers)
    names = {name for files in used.values() for name in files}
    log(f'{len(names)} files on the articles; which are photos ...')
    photos = update.find_photos(names)

    counts = [0, 0, 0]
    sections = []
    for polymer in polymers:
        qid = polymer['qid']
        known = {name for files in linked.get(qid, {}).values() for name in files}
        missing = [(name, sorted(languages, key=ORDER.index))
                   for name, languages in used.get(qid, {}).items()
                   if name in photos and name not in known]
        if not missing:
            continue
        log(qid, polymer['label'], len(missing))
        tiers = [[], [], []]
        for name, languages in sorted(missing, key=lambda m: (-len(m[1]), m[0])):
            tier = 0 if name in lead[qid] else (1 if len(languages) > 1 else 2)
            tiers[tier].append(row(polymer, name, languages, tier == 0))
            counts[tier] += 1
        blocks = ''.join(f'<p class="label">{TIERS[tier]}</p>{"".join(rows)}'
                         for tier, rows in enumerate(tiers) if rows)
        has = ('<span class="has">has a P18 photo</span>' if polymer['photos']
               else '<span class="none">no P18 photo yet</span>')
        sections.append(f'''
  <section class="card">
    <h2><a href="https://www.wikidata.org/wiki/{qid}">{html.escape(polymer['label'])}</a> <span class="muted">{qid}</span> {has}</h2>
    {blocks}
  </section>''')

    intro = (
        'Photos on Wikimedia Commons used on the English, Dutch, German, '
        'French or Italian Wikipedia article of a polymer, but not linked in '
        'Wikidata as image (P18) or chemical structure (P117): '
        f'{sum(counts)} photos for {len(sections)} polymers. {counts[0]} are '
        'the lead image of an article (green border), '
        f'{counts[1]} more are used on two or more Wikipedias, {counts[2]} on '
        'one. Each row has QuickStatements that add the photo as image (P18), '
        'with the Wikipedia it was found on as reference (imported from '
        'Wikimedia project, P143). Copy them, open them in QuickStatements, '
        'or tick rows to collect them in the batch below.')
    curation.write(OUTPUT, curation.page(
        'Polymer Photo Review', 'Photos on Wikipedia, missing in Wikidata',
        intro, ''.join(sections), STYLE, SCRIPT))


if __name__ == '__main__':
    main()
