# MultiNMRFit

[![Documentation Status](https://readthedocs.org/projects/multinmrfit/badge/?version=latest)](http://multinmrfit.readthedocs.io/?badge=latest)
[![Python 3.6+](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)


## What is MultiNMRFit?
MultiNMRFit is a scientific tool designed to extract quantitative information (chemical shifts, signal intensity, coupling constants, etc) from a serie of 1D spectra (acquired individually or as pseudo 2D spectra) by fitting.

It is one of the routine tools that we use for NMR studies of metabolic systems at the [NMR](http://www.toulouse-biotechnology-institute.fr/en/research/physiology-and-engineering-of-microbial-metabolism/rmn.html) and [MetaSys](http://www.toulouse-biotechnology-institute.fr/en/research/physiology-and-engineering-of-microbial-metabolism/metasys.html) teams of the [Toulouse Biotechnology Institute](http://www.toulouse-biotechnology-institute.fr/en/).

The code is open-source, and available under a GPLv3 license. Additional information will be available in an upcoming [publication](https://doi.org/xxx.xxx).

Detailed documentation can be found online at Read the Docs ([https://multinmrfit.readthedocs.io/](https://multinmrfit.readthedocs.io/)).

## Key features
* **fit series of 1D spectra** (acquired as individual 1D spectra, as a pseudo 2D spectrum, or provided as tabulated text files),
* can be used with **all nuclei** (<sup>1</sup>H, <sup>13</sup>C, <sup>15</sup>N, <sup>31</sup>P, etc),
* estimation of several parameters for each signal of interest (**intensity**, **area**, **chemical shift**, **linewidth**, **coupling constant(s)**, etc),
* **semi-automated analysis** for **peak picking** and **definition of multiplicity** for each signal,
* account for **overlaps** between peaks and **zero-order baseline correction**,
* **visual inspection of the fitted curves**,
* estimation of **uncertainty** on estimated parameters (standard deviation),
* shipped as a **library** with a **graphical user interface**,
* open-source, free and easy to install everywhere where Python 3 and pip run,
* biologist-friendly.


## Quick-start
MultiNMRFit requires Python 3.8 or higher and run on all platforms (Windows, MacOS and Unix).
Please check [the documentation](https://multinmrfit.readthedocs.io/en/latest/quickstart.html) for complete
installation and usage instructions.

Use `pip` to **install PhysioFit from GitHub**:

```bash
$ python -m pip install git+https://github.com/NMRTeamTBI/MultiNMRFit
```

Note: Git must be installed on your computer. Have a look to the detailed [documentation](https://multinmrfit.readthedocs.io/en/latest/quickstart.html) for help on installing Git in an Anaconda environment.

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
In preparation, 2024, [doi: xxx.xxxx](https://doi.org/xxx.xxxx)

## Authors
Pierre Millard, Cyril Charlier 

## Contact
:email: charlier@insa-toulouse.fr 
:email: millard@insa-toulouse.fr 
