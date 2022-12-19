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

MultiNMRFit takes as input 1D NMR spectra acquired individually or as a Pseudo2D experiment.
The classical processing steps (baseline correction, phasing, ...) must be performed beforehand in your prefered NMR processing software (e.g. TopSpin). Once the spectra have been processed, 
spectra can be fitted by MultiNMRFit.

..  _`Configuration file`:

Configuration file
================================================================================

The configuration file contains all the required information to load the data (**Inputs** section), run the analysis (**Analysis** section), 
output the results (**Outputs** section). Users might also be interested in tunning some of options (**Options** section). 
The configuration file is a json file (see example below) and contains all rows described below:

:download:`Example file <https://github.com/NMRTeamTBI/MultiNMRFit/blob/dev/multinmrfit/data/Input_example.json>`.

Inputs
--------------------------------------------------------------------------------

:Data path: Path to the directory that contain the data (field "data_path" in the json configuration file)
:Data Folder: Folder containing your NMR data (field "data_folder" in the json configuration file)
:Experiments: List of experiments (expno in Topspin) used in the MultiNMRFit analyis (field "data_exp_no" in the json configuration file)
:Process Number: Process number (procno in Topspin)

Analysis
--------------------------------------------------------------------------------
:Analysis type: Type of experiment (pseudo2D or list of 1D spectra acquired individually) (field "analysis_type" in the json configuration file, which should be 'Pseudo2D' or '1D_Series')
:Reference spectrum: Experiment used as reference for the peak picking and initial fit (field "reference_spectrum" in the json configuration file)
:Spectral limits: Boundaries for the region of spectra to be considered for analysis (field "spectral_limits" in the json configuration file)
:Threshold: Lower limit of intensity for the peak detection (field "threshold" in the json configuration file), i.e. only peaks above this value will be detected

.. topic:: About the type of experiment

          Two types of experiments can be analysed, namely **Pseudo2D** or **1D_Series**. In the case of **Pseudo2D**, a single *Experiments* should be given and all the 
          rows will be processes unless the *Data row no* is provided. The **1D_Series** analysis works for 1D spectra acquired independently. This analysis can 
          also be used to process a single experiment. Specific *Experiments* and *Data row no* to process can be defined as 1,2,3,4 (or 1-4) for complete analysis of experiments 1 to 4, and 1,2,3,4,6
          (or 1-4,6) for partial analysis of specific experiments. 

.. note:: Process Number 
         (e.g. "data_proc_no") should be the same for all experiments.

.. note:: Threshold
         Users will be able to update it through the graphical user interface if needed.
Outputs
--------------------------------------------------------------------------------
:Output path: Path to the directory in which the processing results will be saved (field "output_path" in the json configuration file)
:Output folder: Name of the output folder (field "output_folder" in the json configuration file)
:Output name: Prefix used for all the files created (text files and figures) (field "output_name" in the json configuration file)

Options
--------------------------------------------------------------------------------
:Data row no: Options used for partial processing of a Pseudo2D experiment, in which only a subset of rows need to be analyzed (field "option_data_row_no" in the json configuration file)
:Use previous fit: Use (or not) the fit results of the spectra *i-1* as starting parameters for the fitting of the next spectra *i* (field "option_previous_fit" in the json configuration file, boolean)
:Offset: Consider and estimate (or not) an offset, which corresponds to zero-order baseline correction (field "option_offset" in the json configuration file, boolean)
:Merge pdf(s): Merge (or not) all pdfs in a single file (field "option_merge_pdf" in the json configuration file, boolean)

..  _`MultiNMRFit Analysis`:

MultiNMRFit Analysis
================================================================================

Data Loading
--------------------------------------------------------------------------------
The MultiNMRFit analysis is launched from a terminal (Windows: *Anaconda Prompt*) by using either 
the graphical user interface or the command line. In the first case, an interface will allow the user to 
fill all required information, save the configuration file and run the analysis. 

.. code-block:: bash
  multinmrfit 

If a configuration file already exists (created manually by the user or automatically by MultiNMRFit), it can be loaded directly by providing its path to MultiNMRFit:

.. code-block:: bash
  multinmrfit <path>/<*config_file.json*>

Data visualisation and clustering
--------------------------------------------------------------------------------
A second graphical interface will pop-up to assist the user in the definition of the signals to be considered.  
If the threshold needs to be adapted (lower or higher), just change its value and clic on 'Update threshold'. 

.. note:: Number of peaks
        Number of peaks is by default limited to 15.

The peaks detection is automatically performed on the reference spectrum, within the spectral range provided by the user in the first step. Only peaks with 
an assigned *Cluster ID* will be fitted later on (e.g. by leaving *Cluster ID* it means that the peak is not included in the analysis)

Since coupling phenomena give rise to several peaks for a single signal, the multiplicity of each signal can be defined by setting the same *Cluster ID*
for all peaks of the signal considered. We have currently implemented 
the following multiplicity:

:1 peak: Singlet
:2 peaks: Doublet
:3 peaks: Triplet
:4 peaks: Quadruplet 

.. note:: Cluster ID
        might be defined by integers or string (*xx* for instance)

.. note:: Strong coupling
        is included for a quadruplet by setting the options *Roof* in the menu of at least one of the 4 rows defined with the *Cluster ID*.


Fitting
--------------------------------------------------------------------------------

Spectra analysis starts by fitting all signals defined by the user in the reference spectrum, using information obtained from the peak picking step as starting point for the position, intensities and coupling constants. 
Each multiplicity is defined a sum of signals that are themselves calculated as a weighted average of a lorentzian and gaussian functions (parameter *a*). The procedure also optimizes the **linewidth** (e.g. "lw"), the **ratio** lorentzian/gaussian (e.g. "a"), the **amplitude** (e.g. "Amp"), 
the **center position** of the multiplet (e.g. "x0") and the different **coupling constants** (e.g. "J1, J2").

A window will show the progress 
of the analysis. If the option *option_previous_fit* is selected (by default for a *Pseudo2D* analysis) the fitting of the a spectra *i* will use 
starting parameters the final results of *i-1* otherwise it will always use the results of the reference spectrum as the initial parameters. The use of this option also restrains 
the change of parameters between 2 spectra with for instance J constrained within ±5% of the previous value, x0 within ±1% and lw within ±30%. 

Once the complete analysis is done, MultiNMRFit will automatically plot the fitted and measured spectra and create the text files containing the results.

..  _`Output data`:

Output files
================================================================================

All output files are located in the <*Output folder*> 

Result files
--------------------------------------------------------------------------------

Result file(s) containing the information of interest are tabulated text files named as <*Output name*>_<*multiplicity*>_<*cluster_id*>.txt:
If multiple clusters are defined by the user, one file is created per multiplets. All files contain the following columns:

:exp_no: experiments number 
:proc_no: processing number
:row_id: row number in the Pseudo2D experiments (set as *1* for 1D_Series)
:x0, a, Amp, lw, J1, .., integral: fitting parameters 
:x0_err, a_err, Amp_err, lw_err, J1_err, .., integral_err: error on fitting parameters estimated from covariance matrix
:offset: offset to the baseline if the option is selected 

Plots
--------------------------------------------------------------------------------

All individual plots are displayed in <*plot_ind*> folder which is automatically created. 
If the option *Merge pdf(s)* is selected a single file is created in <*Output name*>_<*Spectra_Full*>.pdf

Log file
--------------------------------------------------------------------------------

A log file *process.log* containing all processing parameters is created for reproducibility and reanalysis.

Warning and error messages
--------------------------------------------------------------------------------

Error messages are explicit. You should examine carefully any warning/error message.
After correcting the problem, you might have to restart MultiNMRFit (to reload files)
and perform the analysis again.
