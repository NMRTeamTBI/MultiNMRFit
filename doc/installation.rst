Installation
============

Installation
-----------------

MultiNMRFit requires Python 3.6 or higher and run on all platforms supporting Python3 (Windows, MacOS and Linux).
If you do not have a Python environment configured on your computer, we recommend that you follow the instructions
from `Anaconda <https://www.anaconda.com/download/>`_.

To install MultiNMRFit using Python's built-in installer, you can just run the following command in a terminal:

.. code-block:: bash

    pip install mulitnmrfit

.. tip::  We recommend the creation of isolated environments for each python tool you install in your system using the python built-in `venv <https://docs.python.org/3/library/venv.html>`_ package or `Anaconda <https://www.anaconda.com/products/individual>`_.

If this method does not work, you should ask your local system administrator or
the IT department "how to install a Python 3 package from PyPi" on your computer.

MultiNMRFit is freely available and is distributed under open-source license at https://github.com/NMRTeamTBI .


Alternatives & updates
----------------------

If yiu want to install the software in development mode, you can use the following command:

.. code-block::

    pip install --3 mulitnmrfit

If you know that you do not have permission to install software system-wide, you can install mulitnmrfit into your user directory using the :samp:`--user` flag:

.. code-block::

    pip install --user mulitnmrfit

This does not require any special privileges.

Once the package is installed, you can update it using the following command:

.. code-block::

    pip install -U mulitnmrfit

Alternatively, you can also download all sources in a tarball from `GitHub <https://github.com/MetaSys-LISBP/PhysioFit>`_,
but it will be more difficult to update PhysioFit later on.