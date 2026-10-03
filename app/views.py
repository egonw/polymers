from decimal import Decimal, InvalidOperation
from urllib.parse import quote, urlsplit

from flask import Blueprint, abort, current_app, render_template

main = Blueprint('app', __name__)

DEPICT = ('https://cdkdepict.toolforge.org/depict/bow/svg?smi={smiles}'
          '&abbr=on&hdisp=bridgehead&showtitle=false&zoom={zoom}'
          '&annotate=none')

COMMONS_PAGE = 'https://commons.wikimedia.org/wiki/File:'
COMMONS_FILE = 'https://commons.wikimedia.org/wiki/Special:FilePath/'

# Names of the Wikipedias that polymer pages link to.
LANGUAGES = {'en': 'English', 'nl': 'Dutch', 'de': 'German', 'fr': 'French',
             'it': 'Italian'}
# The two-letter code shown for each Wikipedia language on the front page:
# the ISO 3166 country code, but EN for English.
COUNTRIES = {'en': 'EN', 'nl': 'NL', 'de': 'DE', 'fr': 'FR', 'it': 'IT'}


@main.app_template_filter('depict')
def depict(cxsmiles, zoom=2):
    """The CDK Depict address of the 2D depiction of a CXSMILES."""
    return DEPICT.format(smiles=quote(cxsmiles, safe=''), zoom=zoom)


@main.app_template_filter('commons_page')
def commons_page(name):
    """The Wikimedia Commons page of a file."""
    return COMMONS_PAGE + quote(name.replace(' ', '_'))


@main.app_template_filter('commons_thumb')
def commons_thumb(name, width=150):
    """A Commons thumbnail of a file; twice the 75 pixels it is shown at, for
    sharp images on high resolution screens."""
    return f'{COMMONS_FILE}{quote(name)}?width={width}'


@main.app_template_filter('attribution')
def attribution(photo):
    """The attribution of a photo, as Commons asks for it: the file, its
    author and its license, for example "Bottle.jpg: Ann, CC BY-SA 4.0, via
    Wikimedia Commons"."""
    text = photo['file']
    if photo.get('artist'):
        text += f": {photo['artist']}"
    if photo.get('license'):
        text += f", {photo['license']}"
    return text + ', via Wikimedia Commons'


@main.app_template_filter('amount')
def amount(value):
    """A Wikidata amount without the ".0" that integers get."""
    return value[:-2] if value.endswith('.0') else value


@main.app_template_filter('domain')
def domain(url):
    """The domain name of an address, to show instead of the address."""
    return urlsplit(url).netloc or url


@main.app_template_filter('quantity')
def quantity(statement):
    """A value with its bounds: "1.2 ± 0.1" or "1.2 (1.1 to 1.4)"."""
    value, lower, upper = (statement.get(key) for key in
                           ('value', 'lower', 'upper'))
    text = amount(value)
    if lower is None or upper is None:
        return text
    try:
        below = Decimal(value) - Decimal(lower)
        above = Decimal(upper) - Decimal(value)
    except InvalidOperation:
        return text
    if below == above:
        return text if below == 0 else f'{text} ± {amount(str(below))}'
    return f'{text} ({amount(lower)} to {amount(upper)})'


def polymers():
    return current_app.config['POLYMERS']


def polymers_by_qid():
    return current_app.config['POLYMERS_BY_QID']


@main.app_context_processor
def globals_for_templates():
    return {'known': polymers_by_qid(), 'languages': LANGUAGES,
            'countries': COUNTRIES}


@main.route('/')
def index():
    with_structure = sum(1 for polymer in polymers() if polymer['cxsmiles'])
    return render_template('index.html', polymers=polymers(),
                           with_structure=with_structure)


@main.route('/<qid>/')
def polymer(qid):
    polymer = polymers_by_qid().get(qid)
    if polymer is None:
        abort(404)
    return render_template('polymer.html', polymer=polymer)


@main.app_errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404
