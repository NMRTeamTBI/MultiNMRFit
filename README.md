# MultiNMRFit

[![PyPI version](https://badge.fury.io/py/multinmrfit.svg)](https://badge.fury.io/py/multinmrfit)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/multinmrfit.svg)](https://pypi.python.org/pypi/multinmrfit/)
[![Documentation Status](https://readthedocs.org/projects/multinmrfit/badge/?version=latest)](http://multinmrfit.readthedocs.io/?badge=latest)


## What is MultiNMRFit?
MultiNMRFit is a scientific tool designed to fit a serie of 1D spectra (acquired individually or as pseudo 2D spectra).

It is one of the routine tools that we use for NMR studies of metabolic systems at the [NMR](http://www.toulouse-biotechnology-institute.fr/en/research/physiology-and-engineering-of-microbial-metabolism/rmn.html) and [MetaSys](http://www.toulouse-biotechnology-institute.fr/en/research/physiology-and-engineering-of-microbial-metabolism/metasys.html) teams and at [MetaToul platform](http://www.metatoul.fr) of the [Toulouse Biotechnology Institute](http://www.toulouse-biotechnology-institute.fr/en/).

The code is open-source, and available under a GPLv3 license. Additional information can be found in the following [publication](https://doi.org/xxx.xxx).

Detailed documentation can be found online at Read the Docs ([https://multinmrfit.readthedocs.io/](https://multinmrfit.readthedocs.io/)).

## Key features
* **fitting of a series of 1D spectra acquired individually or as pseudo 2D spectra**.
* **semi-automated analysis** for **peak picking** and **definition of multiplicity** for each signal.
* account for **overlaps** between peaks.
* **visual inspection of the fitted curves**.
* shipped as a **library** with both a **graphical** and **command line** interface,
* open-source, free and easy to install everywhere where Python 3 and pip run,
* biologist-friendly.

## Quick-start
MultiNMRFit requires Python 3.6 or higher and run on all plate-forms.
Please check [the documentation](https://multinmrfit.readthedocs.io/en/latest/quickstart.html) for complete
installation and usage instructions.

Use `pip` to **install PhysioFit from PyPi**:

```bash
$ pip install multinmrfit
```

Then, start the graphical interface with:

```bash
$ multinmrfit
```

MultiNMRFit is also available as a Python library.

## Bug and feature requests
If you have an idea on how we could improve MultiNMRFit please submit a new *issue*
to [our GitHub issue tracker](https://github.com/NMRTeamTBI/MultiNMRFit/issues).


## Developers guide
### Contributions
Contributions are very welcome! :heart:


### Local install with pip
In development mode, do a `pip install -e /path/to/MultiNMRFit` to install
locally the development version.

### Build the documentation locally
Build the HTML documentation with:

```bash
$ cd doc
$ make html
```

The PDF documentation can be built locally by replacing `html` by `latexpdf`
in the command above. You will need a recent latex installation.

## How to cite
Ref, 2022, [doi: xxx.xxxx](https://doi.org/xxx.xxxx)

## Authors
Cyril Charlier, Pierre Millard

## Contact
:email: charlier@insa-toulouse.fr