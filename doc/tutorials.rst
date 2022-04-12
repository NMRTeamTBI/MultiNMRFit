..  _Tutorials:

################################################################################
Tutorials
################################################################################

.. seealso:: If you have a question that is not covered in the tutorials, have a look
             at the :ref:`faq` or please contact us.


.. _First time using MultiNMRFit:

********************************************************************************
First time using MultiNMRFit
********************************************************************************

..  _`Input data`:

Input data
================================================================================

MultiNMRFit takes as input processed 1D NMR data either acquired in a Pseudo2D manner or a list of 1D experiments acquired separetly.
MultiNMRFit assumes that all the processing (base line correction, phasing, ...) is performed prior its usage.

..  _`Configuration file`:

Configuration file
================================================================================

The configuration file contains all the required information to load the data (**Inputs** section), run the analysis (**Analysis** section), 
output the results (**Outputs** section). Users might alos be intersted to use some of the options (**Options** section). 
The configuration file is a json file (see example below) and contains all rows described below:

:download:`Example file <../multinmrfit/data/Imput_example.json>`.

Inputs
--------------------------------------------------------------------------------

:Data path: Path to the directory that contain the data; e.g. "data_path"
:Data Folder: Folder containing your NMR data; e.g. "data_folder"
:Experiments: List of experiments used in the MultiNMRFit analyis; e.g. "data_exp_no"
:Process Number: Process number (e.g. procno in Topspin); e.g. "data_proc_no"

Analysis
--------------------------------------------------------------------------------
:Analysis type: Choice of analysis between a pseudo2D or list of 1D experiments; e.g. "analysis_type" (Pseudo2D or 1D_Series)
:Reference spectrum: Experiment used for the peak picking and initial fit; e.g. "reference_spectrum"
:Spectral limits: Boundaries for the region of spectra to be used in the analysis; e.g. "spectral_limits"
:Threshold: Lower limit for the peak detection; e.g. "threshold"

.. topic:: About Analysis

          Two type of analysis type are provided **Pseudo2D** or **1D_Series**. In the case of **Pseudo2D** analysis a single *Experiments* should be given and all the 
          rows will be processes unless the *Data row no* is defined. The **1D_Series** analysis works for 1D 1H experiments acquired independently. This analysis should 
          also be used for a the fitting of a single experiment. *Experiments* might be defined as 1,2,3,4,5,6,7,8,9,10 (or 1-10) for sequential experiments and 1,5,6,7,8,9,10
          (1,5-10) for incomplete series. 

.. note:: Process Number 
         (e.g. "data_proc_no") should be the same for all experiments.

.. note:: Threshold
         Users will be able to update it through the graphical user interface is needed.
Outputs
--------------------------------------------------------------------------------
:Output path: Path to the directory in which the outputs of the program will be saved; e.g. "output_path"
:Output folder: Folder for the outputs; e.g. "output_folder"
:Output name: Name used for all the filed created (text files and figures); e.g. "output_name"

Options
--------------------------------------------------------------------------------
:Data row no: Options used in the case of incomplete processing of a Pseudo2D experiments, in which only a subset of rows need to be analyzed; e.g. "option_data_row_no"
:Use previous fit: Options for the analysis to use the fit of the row *i-1* as a starting parameter for the fitting of row *i*; e.g. "option_previous_fit"
:Offset: Adding an offset in the fitting (otherwise set to 0 by default); e.g. "option_offset"
:Merge pdf(s): Options used to merge all pdfs in a single file; e.g. "option_merge_pdf"

..  _`MultiNMRFit Analysis`:

MultiNMRFit Analysis
================================================================================

Data Loading
--------------------------------------------------------------------------------
The MultiNMRFit analysis is launched from a terminal (Windows: *Anaconda Prompt*) either by using 
the graphical user interface or the command line. In the first case, a interface will allow the user to 
fill all required information, save the configuration file and run the analysis. 

.. code-block:: bash
  multinmrfit 

In the second instance, the configuration file already exists and the analysis might be started from the command line.

.. code-block:: bash
  multinmrfit <path>/<*config_file.json*>

Data visualisation and clustering
--------------------------------------------------------------------------------

Multiplets
--------------------------------------------------------------------------------

The mulitplicity of each cluster is automatically defined by the number of repetitions of the same *Cluster ID*
in the *Peak Picking visualisation and Clustering*. 

.. note:: Cluster ID
         The Cluster ID might be defined by integers or string (*xx* for instance)

At this stage 


..  _`Output data`:

Output files
================================================================================

Result file
--------------------------------------------------------------------------------
All output are located in the <*Output folder*> 

Result file(s) are txt files name as <*Output name*>_<*multiplicity*>_<*cluster_id*>.txt:
If multiple clusters are defined by the user one file per multiplets is created and they all contain the following columns:

:exp_no: experiments number 
:proc_no: processing number
:row_id: row number in the Pseudo2D experiments (set as *1* for 1D_Series)
:x0, a, Amp, lw, J1, .., integral: fitting parameters 
:x0_err, a_err, Amp_err, lw_err, J1_err, .., integral_err: error on fitting parameters estimated from covariance matrix
:offset: offset to the baseline if the option is selected 

Result file
--------------------------------------------------------------------------------

All individual plots are displayed in <*plot_ind*> folder which is automatically created. 
If the option *Merge pdf(s)* is selected a single file is created in <*Output name*>_<*Spectra_Full*>.pdf

--------------------------------------------------------------------------------

A log file is created in the same directory <*Output name*> to store all parameters (for reproducibility),
in file a *process.log*.

Warning and error messages
--------------------------------------------------------------------------------

Error messages are explicit. You should examine carefully any warning/error message.
After correcting the problem, you might have to restart MultiNMRFit (to reload files)
and perform the analysis again.
