PYTHON ?= venv/bin/python

.PHONY: all update build serve test clean venv

all: build

venv:
	python3 -m venv venv
	venv/bin/pip install -r requirements.txt

# Ask Wikidata (QLever) for the polymers and write _data/polymers.json.
update:
	$(PYTHON) scripts/update_polymers.py

# Write the static website to build/, for GitHub Pages.
build:
	$(PYTHON) freeze.py

# Run the website at http://localhost:8200/.
serve:
	$(PYTHON) runserver.py

test:
	$(PYTHON) -m unittest discover -s tests -v

clean:
	rm -rf build
