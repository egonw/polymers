# Polymers

This is a Wikidata-powered database of polymers with their physicochemical properties, backed
by scientific literature.

Wikidata captures polymers ([wd:Q81163](http://www.wikidata.org/entity/Q81163)) as materals composed of a
group or class of chemical substances ([wd:Q17339814](http://www.wikidata.org/entity/Q17339814)).
An example polymer is poly(p-phenylene oxide) ([wd:Q146206](http://www.wikidata.org/entity/Q146206)),
and has the chemical structural representation with CXSMILES. The CXSMILES is machine readable and
can be converted to an image with CDK Depict.

An example class of polymers is polycarbonate ([wd:Q62246](http://www.wikidata.org/entity/Q62246)),
which is group of polymers that all include a carbonate functionality in the repeating unit.

Polymers have properties including:

* thermal conductivity ([wd:P2068](http://www.wikidata.org/entity/P2068))
* specific heat capacity ([wd:P2056](http://www.wikidata.org/entity/P2056))
* density ([wd:P2054](http://www.wikidata.org/entity/P2054))
* refractive index ([wd:P1109](http://www.wikidata.org/entity/P1109))

## The website

The website is a small [Flask](https://flask.palletsprojects.com/) application that is published as
static HTML on GitHub Pages. The front page lists the polymers, three next to each other, with their
name, a 2D depiction made by [CDK Depict](https://cdkdepict.toolforge.org/) and the CXSMILES from
Wikidata. Every polymer has its own page with its structure, identifiers (CAS, ChEBI, PubChem), the
polymer classes and monomers, and a table of its physicochemical properties: the value with its
unit, the conditions (qualifiers such as the temperature) and the source with its DOI.

The polymers are the items that are an instance of polymer ([wd:Q81163](http://www.wikidata.org/entity/Q81163))
or of type of polymer ([wd:Q119896085](http://www.wikidata.org/entity/Q119896085)), and the items
that are an instance of another subclass of polymer and have a CXSMILES. (Every instance of a
subclass of polymer would include a million proteins and RNAs.) The properties are all quantity
statements of the best rank.

### Running it

Requires Python 3.

```shell
make venv      # create venv/ and install the requirements
make serve     # run the website at http://localhost:8200/
make build     # write the static website to build/
make test      # run the tests
```

### Updating the data

The data is stored in [_data/polymers.json](_data/polymers.json), one record per polymer, sorted by
QID. Update it with:

```shell
make update
```

This runs [scripts/update_polymers.py](scripts/update_polymers.py), which asks the
[QLever instance of Wikidata](https://qlever.dev/wikidata) the queries in [sparql/](sparql/): the
polymers (`polymers.rq`), their quantity statements (`properties.rq`), and the references
(`references.rq`) and qualifiers (`qualifiers.rq`) of those statements. The last two get the
statements in a `VALUES` clause, because asking for everything in one query makes QLever time
out. English labels are used, and the `mul` label when there is no English one. Commit the
changed JSON to publish it.

### Publishing

The workflow [.github/workflows/pages.yml](.github/workflows/pages.yml) runs the tests, builds the
website with [Frozen-Flask](https://frozen-flask.readthedocs.io/) and publishes `build/` on every
push to `main`. Set *Settings > Pages > Source* to *GitHub Actions* once. The links in the pages
are relative, so the website works at any address.

## Use of LLMs

This web application is created with the help of LLMs, but the authors take full responsibility of all functionality.
