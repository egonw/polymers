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
name, a 2D depiction made by [CDK Depict](https://cdkdepict.toolforge.org/) of the CXSMILES from
Wikidata and, when Wikidata has one, a photo (P18) as a 75 by 75 pixel cutout that links to its
page on Wikimedia Commons. Many images in Wikidata are 2D drawings of the structure instead, so
the update script asks Commons whether a file is a photo: its structured data says it is an
instance of photograph ([wd:Q125191](http://www.wikidata.org/entity/Q125191)) or of scanning
electron micrograph, its metadata names a camera, or its description or categories mention a
photo. A photo that does not show up can be fixed on Commons by adding "instance of: photograph"
to its structured data. Every polymer has its own page with its structure, identifiers (CAS, ChEBI, PubChem CID and SID), the
polymer classes and monomers, links to the English, Dutch, German, French and Italian Wikipedia,
and a table of its physicochemical properties: the value with its
unit, the conditions (qualifiers such as the temperature) and the source with its DOI.
Polymers that are a class of polymers, such as nylon ([wd:Q177941](http://www.wikidata.org/entity/Q177941)),
also get a grid of the polymers in that class: every item that is a subclass (P279) or an instance
(P31) of it, recursively. That grid is the same as the one on the front page, and is in
[_includes/polymer_grid.html](_includes/polymer_grid.html). Members that have no page on this
website (many are brands or grades) link to Wikidata.

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
polymers (`polymers.rq`), the members of the classes of polymers (`members.rq`), their quantity
statements (`properties.rq`), and the references
(`references.rq`) and qualifiers (`qualifiers.rq`) of those statements. The last two get the
statements in a `VALUES` clause, because asking for everything in one query makes QLever time
out. English labels are used, and the `mul` label when there is no English one. Commit the
changed JSON to publish it.

### Curation reports

```shell
make curate
```

writes two pages that help to improve the polymer data in Wikidata. Both are single HTML files,
with the images included, that can be opened from disk:

* [cxsmiles-comparison.html](cxsmiles-comparison.html) ([scripts/curate_cxsmiles.py](scripts/curate_cxsmiles.py)):
  for every polymer with a chemical structure image (P117), that image next to the drawing of its
  CXSMILES by CDK Depict, to check that they match, and to see which polymers still need a
  CXSMILES. CXSMILES that are proposed but not yet in Wikidata can be put in `polymers.qs`, as
  QuickStatements (`Qxxx<TAB>P10718<TAB>"cxsmiles"`), and are then shown too.
* [wikipedia-photos.html](wikipedia-photos.html) ([scripts/curate_photos.py](scripts/curate_photos.py)):
  the photos on Commons that are used on the English, Dutch, German, French or Italian Wikipedia
  article of a polymer, but are not its image (P18) or chemical structure (P117) in Wikidata, with
  links to the articles and, for each photo, QuickStatements that add it as image, with the
  Wikipedia as reference. Rows can be collected into one batch.

The reports use [_data/polymers.json](_data/polymers.json), so run `make update` first for the
newest data. The images that the reports include are downloaded once into `cache/` (ignored by
git); delete that folder to download them again. Wikimedia limits how fast its servers may be
asked, so a run takes several minutes.

### Publishing

The workflow [.github/workflows/pages.yml](.github/workflows/pages.yml) runs the tests, builds the
website with [Frozen-Flask](https://frozen-flask.readthedocs.io/) and publishes `build/` on every
push to `main`. Set *Settings > Pages > Source* to *GitHub Actions* once. The links in the pages
are relative, so the website works at any address.

## License and citation

The code is released under the GNU General Public License version 3, see [LICENSE.md](LICENSE.md),
the same license as [Scholia](https://github.com/WDscholia/scholia). The data comes from Wikidata
(CC0). If you use this website, please cite the Scholia Chemistry article it is based on, as given
in [CITATION.cff](CITATION.cff): Willighagen et al., *Scholia Chemistry: access to chemistry in
Wikidata*, ChemRxiv (2025), [doi:10.26434/chemrxiv-2025-53n0w](https://doi.org/10.26434/chemrxiv-2025-53n0w).

## Use of LLMs

This web application is created with the help of LLMs, but the authors take full responsibility of all functionality.
