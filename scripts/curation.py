"""Shared parts of the curation reports (make curate): the polymers, the
images Wikidata links for them, downloads with retries, and images embedded
as base64 so that the reports work as single files.
"""

import base64
import hashlib
import json
import sys
import time
from collections import defaultdict
from urllib.parse import quote, unquote

import requests

import update_polymers as update

ROOT = update.ROOT
# Downloaded images, so that a report can be made again without asking
# Wikimedia for all of them; delete the folder to download them again.
CACHE = ROOT / 'cache' / 'images'
# Seconds between downloads of images that are not in the cache yet, to stay
# below the rate limits of Wikimedia.
DOWNLOAD_PAUSE = 0.5

COMMONS_PAGE = 'https://commons.wikimedia.org/wiki/File:'
COMMONS_FILE = 'https://commons.wikimedia.org/wiki/Special:FilePath/'

# The page style shared by the reports, after that of the website.
STYLE = '''
:root { --bg:#f5f6f8; --card:#fff; --text:#1f2933; --muted:#6b7785; --border:#dde1e6;
        --accent:#2563eb; --code:#f0f2f5; --lead:#15803d; --flag:#b45309; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#14181d; --card:#1d232a; --text:#e6e9ed; --muted:#97a3b0; --border:#2f3842;
          --accent:#6ea0ff; --code:#262d35; --lead:#4ade80; --flag:#f59e0b; } }
* { box-sizing:border-box; }
body { margin:0; padding:2rem 1rem; background:var(--bg); color:var(--text);
       font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
main { max-width:64rem; margin:0 auto; }
h1 { margin:0 0 .5rem; font-size:1.5rem; font-weight:600; }
h2 { margin:0 0 .5rem; font-size:1.1rem; font-weight:600; }
a { color:var(--accent); }
.muted { color:var(--muted); font-weight:400; font-size:.9rem; }
.intro { margin:0 0 1.5rem; color:var(--muted); }
.card { margin-bottom:1rem; padding:1.25rem; background:var(--card);
        border:1px solid var(--border); border-radius:8px; }
.label { margin:1rem 0 .4rem; font-size:.75rem; letter-spacing:.08em;
         text-transform:uppercase; color:var(--muted); }
code { display:block; padding:.35rem .5rem; background:var(--code); border-radius:4px;
       font:.78rem/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
       overflow-wrap:anywhere; white-space:pre-wrap; tab-size:2; }
.flag { color:var(--flag); }
'''


def log(*args):
    print(*args, file=sys.stderr)


def load_polymers():
    with open(update.OUTPUT, encoding='utf-8') as file:
        return json.load(file)


def file_name(url):
    """The Commons file name of a Special:FilePath address."""
    return unquote(url.rsplit('/', 1)[1]).replace('_', ' ')


def linked_images(polymers):
    """The images Wikidata links for the polymers, as {qid: {property:
    [file names]}}, for image (P18) and chemical structure (P117)."""
    values = ' '.join(f'wd:{polymer["qid"]}' for polymer in polymers)
    query = update.read_query('images.rq').replace('{{polymers}}', values)
    images = defaultdict(lambda: defaultdict(list))
    for row in update.run_query(query):
        update.add_unique(images[row['polymer']][row['property']],
                          file_name(row['file']))
    for files in images.values():
        for names in files.values():
            names.sort()
    return images


def request(method, url, **kwargs):
    """An HTTP request that waits and tries again when the server is busy,
    as Wikimedia often is when many images are asked for."""
    headers = {'User-Agent': update.USER_AGENT}
    for wait in update.RETRY_WAITS + (None,):
        response = requests.request(method, url, headers=headers,
                                    timeout=update.TIMEOUT, **kwargs)
        if response.status_code not in (429, 503) or wait is None:
            break
        # Wikimedia asks to try again after a second, but is then still
        # busy; waiting longer gets through with fewer requests.
        retry_after = response.headers.get('Retry-After', '')
        if retry_after.isdigit():
            wait = max(wait, int(retry_after))
        log(f'  {response.status_code} from {url.split("/")[2]}, '
            f'trying again in {wait} s')
        time.sleep(wait)
    response.raise_for_status()
    return response


def data_uri(url):
    """The image at an address as a base64 data URI, downloaded once."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / hashlib.sha1(url.encode()).hexdigest()
    if not cached.exists():
        response = request('GET', url)
        kind = response.headers.get('Content-Type', 'image/png').split(';')[0]
        cached.write_bytes(kind.encode() + b'\n' + response.content)
        time.sleep(DOWNLOAD_PAUSE)
    kind, data = cached.read_bytes().split(b'\n', 1)
    return f'data:{kind.decode()};base64,' + base64.b64encode(data).decode()


def commons_page(name):
    return COMMONS_PAGE + quote(name.replace(' ', '_'))


def commons_thumb(name, width):
    return data_uri(f'{COMMONS_FILE}{quote(name)}?width={width}')


def depiction(cxsmiles):
    """The CDK Depict drawing of a CXSMILES, as in the website."""
    sys.path.insert(0, str(ROOT))
    from app.views import DEPICT
    url = DEPICT.format(smiles=quote(cxsmiles, safe=''), zoom=2)
    return data_uri(url.replace('/depict/bow/svg?', '/depict/bow/png?'))


def page(title, heading, intro, body, style='', script=''):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>{STYLE}{style}</style>
</head>
<body>
<main>
  <h1>{heading}</h1>
  <p class="intro">{intro}</p>
  {body}
</main>
{script}
</body>
</html>
'''


def write(path, text):
    path.write_text(text, encoding='utf-8')
    log(f'Wrote {path.relative_to(ROOT)} '
        f'({path.stat().st_size // 1024} kB)')
