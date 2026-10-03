import json
from pathlib import Path

from flask import Flask

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / '_data' / 'polymers.json'


def create_app(data_path=DEFAULT_DATA):
    app = Flask(__name__)
    # Relative links, so the frozen site works under any GitHub Pages path.
    app.config['FREEZER_RELATIVE_URLS'] = True
    app.config['FREEZER_DESTINATION'] = str(ROOT / 'build')

    with open(data_path, encoding='utf-8') as file:
        polymers = json.load(file)
    app.config['POLYMERS'] = polymers
    app.config['POLYMERS_BY_QID'] = {p['qid']: p for p in polymers}

    from .views import main
    app.register_blueprint(main)

    return app
