MultiNMRFit: automated analysis of NMR spectra.
********************************************************************************

Welcome to MultiNMRFit documentation!
----------------------------------------

**MultiNMRFit is a scientific software dedicated to the analysis of NMR data**. It is one of the routine tools that we use at the `NMR team <https://www.toulouse-biotechnology-institute.fr/en/poles/equipe-rmn-2/>`_ and `MetaSys team <https://www.toulouse-biotechnology-institute.fr/en/poles/equipe-metasys/>`_ of `Toulouse Biotechnology Institute <http://www.toulouse-biotechnology-institute.fr/en/>`_.

The code is open-source, and available on `GitHub <https://github.com/NMRTeamTBI/MultiNMRFit>`_ under a :ref:`GPLv3 license <license>`.

This documentation is available on Read the Docs (`https://multinmrfit.readthedocs.io <https://multinmrfit.readthedocs.io/>`_)
and can be downloaded as a `PDF file <https://multinmrfit.readthedocs.io/_/downloads/en/latest/pdf/>`_.


**Key features**

* **fit series of 1D spectra** (acquired as individual 1D spectra, as a pseudo 2D spectrum, or provided as tabulated text files),
* can be used with **all nuclei** (:sup:`1`\ H, :sup:`13`\ C, :sup:`15`\ N, :sup:`31`\ P, etc),
* estimation of several parameters for each signal of interest (**intensity**, **area**, **chemical shift**, **linewidth**, **coupling constant(s)**, etc),
* **semi-automated analysis** for **peak picking** and **definition of multiplicity** for each signal,
* account for **overlaps** between peaks and **zero-order baseline correction**,
* **visual inspection of the fitted curves**,
* estimation of **uncertainty** on estimated parameters (standard deviation),
* shipped as a **library** with a **graphical user interface**,
* open-source, free and easy to install everywhere where Python 3 and pip run,
* biologist-friendly.

.. rubric:: See Also
We strongly encourage you to read the :ref:`Tutorials` before using MultiNMRFit.

.. toctree::
   :maxdepth: 2
   :caption: Usage

   quickstart.rst
   tutorials.rst
   models.rst
   cite.rst
   
.. toctree::
   :maxdepth: 1
   :caption: Miscellaneous

   faq.rst
   library.rst
   license.rst

.. todolist::
