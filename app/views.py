from decimal import Decimal, InvalidOperation
from urllib.parse import quote, urlsplit

from flask import Blueprint, abort, current_app, render_template

main = Blueprint('app', __name__)

DEPICT = ('https://cdkdepict.toolforge.org/depict/bow/svg?smi={smiles}'
          '&abbr=on&hdisp=bridgehead&showtitle=false&zoom={zoom}'
          '&annotate=none')

# Names of the Wikipedias that polymer pages link to.
LANGUAGES = {'en': 'English', 'nl': 'Dutch', 'de': 'German', 'fr': 'French',
             'it': 'Italian'}
# The ISO 3166 country code shown for each Wikipedia language on the front
# page; English gets the United Kingdom.
COUNTRIES = {'en': 'GB', 'nl': 'NL', 'de': 'DE', 'fr': 'FR', 'it': 'IT'}


@main.app_template_filter('depict')
def depict(cxsmiles, zoom=2):
    """The CDK Depict address of the 2D depiction of a CXSMILES."""
    return DEPICT.format(smiles=quote(cxsmiles, safe=''), zoom=zoom)


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


@main.route('/')
def index():
    with_structure = sum(1 for polymer in polymers() if polymer['cxsmiles'])
    return render_template('index.html', polymers=polymers(),
                           with_structure=with_structure,
                           languages=LANGUAGES, countries=COUNTRIES)


@main.route('/<qid>/')
def polymer(qid):
    polymer = polymers_by_qid().get(qid)
    if polymer is None:
        abort(404)
    return render_template('polymer.html', polymer=polymer,
                           known=polymers_by_qid(), languages=LANGUAGES)


@main.app_errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404
