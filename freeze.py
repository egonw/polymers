"""Writes the website as static HTML files to build/, for GitHub Pages."""

from pathlib import Path

from flask_frozen import Freezer

from app import create_app

app = create_app()
freezer = Freezer(app)


@freezer.register_generator
def polymer():
    for item in app.config['POLYMERS']:
        yield 'app.polymer', {'qid': item['qid']}


if __name__ == '__main__':
    freezer.freeze()
    # GitHub Pages should serve the files as they are, without Jekyll.
    (Path(app.config['FREEZER_DESTINATION']) / '.nojekyll').touch()
