MultiNMRFit: Fitting of 1D NMR Data
********************************************************************************

Welcome to MultiNMRFit documentation!
----------------------------------------

.. image:: _static/toc_multinmrfit.png
   :width: 100%
   :align: center

|

**MultiNMRFit is a scientific software dedicated to the analysis of 1H NMR data **.

MultiNMRFit is a scientific tool designed to extract quantitative information (chemical shifts, signal intensity, coupling constants, etc) from a serie of 1D spectra (acquired individually or as pseudo 2D spectra) by fitting.

It is one of the routine tools that we use for NMR studies of metabolic systems at the [NMR](http://www.toulouse-biotechnology-institute.fr/en/research/physiology-and-engineering-of-microbial-metabolism/rmn.html) and [MetaSys](http://www.toulouse-biotechnology-institute.fr/en/research/physiology-and-engineering-of-microbial-metabolism/metasys.html) teams and at [MetaToul platform](http://www.metatoul.fr) of the [Toulouse Biotechnology Institute](http://www.toulouse-biotechnology-institute.fr/en/).

The code is open-source, and available under a GPLv3 license. Additional information can be found in the following [publication](https://doi.org/xxx.xxx).

This documentation is available on Read the Docs (`https://multinmrfit.readthedocs.io <https://multinmrfit.readthedocs.io/>`_)
and can be downloaded as a `PDF file <https://multinmrfit.readthedocs.io/_/downloads/en/latest/pdf/>`_.


.. rubric:: Key features

* **fitting of a series of 1D spectra (acquired individually or as a pseudo 2D spectra)**,
* estimation of several parameters (**intensity**, **area**, **chemical shift**, **linewidth**, **coupling constant(s)**, **offset**, etc) for each signal of interest,
* **semi-automated analysis** for **peak picking** and **definition of multiplicity** for each signal,
* account for **overlaps** between peaks and **zero-order baseline correction**,
* **visual inspection of the fitted curves**,
* estimation of **uncertainty** (standard deviation) on estimated parameters,
* shipped as a **library** with both a **graphical** and **command line** interface,
* open-source, free and easy to install everywhere where Python 3 and pip run,
* biologist-friendly.

.. seealso:: We strongly encourage you to read the :ref:`Tutorials` before using MultiNMRFit.

.. toctree::
   :maxdepth: 2
   :caption: Usage

   quickstart.rst
   tutorials.rst
   cite.rst

.. toctree::
   :maxdepth: 1
   :caption: Miscellaneous

   faq.rst
   definitions.rst
   library_doc.rst
   license.rst

.. todolist::
