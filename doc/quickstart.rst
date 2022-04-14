..  _Quick start:

Quick start
********************************************************************************


Installation
------------------------------------------------

MultiNMRFit requires Python 3.6 or higher. If you do not have a Python environment
configured on your computer, we recommend that you follow the instructions
from `Anaconda <https://www.anaconda.com/download/>`_.

Then, open a terminal (e.g. run *Anaconda Prompt* if you have installed Anaconda) and type:

.. code-block:: bash

  pip install multinmrfit

You are now ready to start MultiNMRFit.

If this method does not work, you should ask your local system administrator or
the IT department "how to install a Python 3 package from PyPi" on your computer.

Alternatives & update
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you know that you do not have permission to install software systemwide,
you can install MultiNMRFit into your user directory using the :samp:`--user` flag:

.. code-block:: bash

  pip install --user multinmrfit


If you already have a previous version of MultiNMRFit installed, you can upgrade it to the latest version with:

.. code-block:: bash

  pip install --upgrade multinmrfit


Alternatively, you can also download all sources in a tarball from `GitHub <https://github.com/NMRTeamTBI/MultiNMRFit>`_,
but it will be more difficult to update MultiNMRFit later on.


Usage
------------------------------------------------

*Data Loading* via Graphical User Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To start the Graphical User Interface, type in a terminal (Windows: *Anaconda Prompt*):

.. code-block:: bash

  multinmrfit

The MultiNMRFit window will open. If the window fails to open, have a look at our
:ref:`dedicated troubleshooting procedure <failed_gui>` to solve the problem.

.. image:: _static/multinmrfit_load_gui.png

Fill al the required entries from the **inputs**, **analysis** and **outputs** sections. **Options** might me used accordingly to your need and 
click on :samp:`Run`. If you want to save your configuration file click on :samp:`Save` and a small window will pop up in which you can specify the file name. 
If your confconfigurationig file is already created, click on :samp:`Load` that will fill all fields. 

.. note:: The configuration file is not saved automatically.

Click on the :samp:`Run` button to go to the next step and display the visualization and clustering window (see below).

.. note:: MultiNMRFit silently overwrites (results and log) files if they already exist. So take care to copy your results elsewhere if you want to protect them from overwriting.

*Data Loading* via Command Line Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To process your data, type in a terminal:

.. code-block:: bash

  multinmrfit [path/to/your/configuration_file.json]

where :samp:`path/configuration_file.json` is the path to the file that contains all processing options.

MultiNMRFit will directly display the visualization and clustering window (see below).

.. seealso:: See tutorial :ref:`First time using MultiNMRFit` for an example of configuration file.

*Peak Picking visualisation and Clustering* via Graphical User Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. image:: _static/multinmrfit_clustering_gui.png

MultiNMRFit automatically detects peaks above the threshold given previously either through the loading ui or in the configuration file. 
If the **threshold** is too low (c.a no peaks are detected) you need to decrease the threshold value (bottom left entry) and click on :samp:`Update Threshold`
to perform the peak picking with the updated threshold value. Detected peaks are marked with a colored dot on the spectrum and appear in the **clustering information** table. 
Peaks are labeled with the same color as on the plot and appear in the chemical shift ascending manner (c.a from right to left).

Once you have filled at least one **cluster ID** click on :samp:`Run Fitting` to start data analysis. A progress bars will display the fitting progress and more information are displayed in the terminal.


Library
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

MultiNMRFit is also available as a library (a Python module) that you can import directly in your Python
scripts:

.. code-block:: python

  import multinmrfit
