..  _Tutorials:

################################################################################
Tutorial
################################################################################

.. seealso:: If you have a question that is not covered in the tutorials, have a look
             at the :ref:`faq` or please contact us.

This tutorial will guide you through the different pages of MultiNMRFit interface. 

.. _Inputs & Outputs:

********************************************************************************
Inputs & Outputs
********************************************************************************

..  _`Data type`:

Data type
================================================================================
MultiNMRFit assumes that all the processing (base line correction, phasing, ...) is performed prior its usage.
MultiNMRFit can load 1D NMR data in 3 formats:

        * **Pseudo2D**: pseudo2D experiment (Bruker format only),
        * **list of 1Ds**: list of 1Ds acquired independently (Bruker format only), 
        * **txt data**: data from a text tabulated file (:file:'.txt' extension) with the following structure:

+-------+-------+-------+-------+
|  ppm  |   0   |  ...  |    n  |
+=======+=======+=======+=======+
|  0    | 1.2e3 |   ... | 1.2e6 |
+-------+-------+-------+-------+
|  0.1  | 1.3e3 |   ... |  4e7  |
+-------+-------+-------+-------+
|  0.2  |   2e8 |   ... | 3.6e3 |
+-------+-------+-------+-------+
|  ...  | ...   |   ... |  ...  |
+-------+-------+-------+-------+
|  12   |   3e4 |   ... | 7.85e3|
+-------+-------+-------+-------+

The column **ppm** is mandatory and contains the ppm scale assumes to be same for all spectra. 
The follwing columns here names **0** to **n** correspond to each individual spectra that will be loaded into MultiNMRFit


.. note:: **list of 1Ds**:  
        The list of  experiments should be provided as 
        * 1,8,109 : for non-consecutive 
        * 1-5 : sequential se experiments (resulting in 1,2,3,4,5)
        * 1-5,109 : for incomplete series (resulting in 1,2,3,4,5,109) 

.. warning:: **list of 1Ds**  
        All the data needs to have the same number of points (**TD**) and the ppm scale identical. 
        If data were processes with different **SR** parameters in TopSpin it might shift one dataset to another.
        The ppm scale will be taken from the first experiment in the list.

..  _`Inputs/Outputs`:

Inputs/Outputs
================================================================================

:data_path: Path to the directory that contain the data
:data_folder: Folder containing your NMR data
:expno: List of experiments used in the MultiNMRFit analyis
:procno: Process number (e.g. procno in Topspin)

.. note:: **Inputs**:  
        The different fields will for inputs as described above will appear only for data type (**Pseudo2D** & **list of 1Ds**)
        For **txt data**, the text file must be loaded using the drag-and-drop menu. 


.. note:: **procno**:  
        If a list of **expno** is provided the **procno** needs to be same for all the **expnos**.

:output_path: path to the folder use to export the outputs
:output_folder: folder with the outputs
:filename: name of the pickle file containing the process that will be automatically saved through the workflow.

Load a processing file
================================================================================

Along the way the process is saved in a pickle format containing the entire process that was perfomed. 
The pickle file can be loaded using the drag-and-drop menu available in side bar of the Inputs & Outputs page. 

Once you are ready to load the spectrum, clicked the **Load Spectrum** buttom.

.. _Process ref. spectrum:

.. ********************************************************************************
.. Inputs & Outputs
.. ********************************************************************************

Once the data are correctly loaded the second page of the interface becomes available and allows use to perform the fitting of the reference spectrum:

.. image:: _static/Set_ref_processing.jpg
  :scale: 60%

The top part of this page automatically performs the peak picking on the reference spectrum within the region displayed in the graph:
* **Select reference spectrum**: Select one the spectrum of the list. Tis specturm (called reference spectrum) will be used for automatic peak detection and initial fitting. 
* **Select region to (re)process**: Multiple independent regions can be processed. Here, it will give you the choice of all regions added to the process.  
* **Spectral limits (max)**: Maximum of the spectral window (default is the maximum of the ppm scale)
* **Spectral limits (min)**: Minimum of the spectral window (default is the min of the ppm scale)

.. note:: **reference spectrum**:  
        The signal that you to analyze needs to be seen in the reference spectrum.
.. note:: **spectral limits**:  
        The difference betwwen the max and min should be at least 0.25 ppm.

You can adjust the **Peak picking threshold** to detect the desired peaks on the displayed spectrum. 

While adjusting this threshold the software will automatically display a dataframe **Peak list** with the detected peaks in the region (marked with a yellow triangle on the spectrum).
The peaks are displayed in the ascending order (e.g. from right to left on the spectrum).

You can now proceed with the clustering steps that consists in filling out the **cluster ID** column of the **Peak list** to group peaks together. Peaks that belongs to the same multiplets 
must have the same names.

.. note:: **cluster ID**:  
        Cluter IDs can be anything (numbers or string).

Once this clustering is performed press the **Assign peaks** button to move towards the model construction:

.. image:: _static/model_construction.jpg
  :scale: 60%

For each cluster MultiNMRFit will provide a choice of all the models containing this number of peaks and will give you the choice to add a offset to fit.
This offset is equivalent to a linear phase correction on the selected window. Once this step is done, you can click on the **Build model** button 
that will automatically creates the fitting model and initially display the table of fitting parameters (at this step initial values along with boundaries).

.. image:: _static/fitting_parameters.jpg
  :scale: 60%

Intitial values are calculated based on [i] the results of the peak picking (intensities and peak position) [ii] the default parameters of the each model
(look at :doc:`models.rst` for more details on the default parameters). If no changes are required press the **Fit spectrum** button to proceed with the minimization
of the reference spectrum. 

.. note:: **Parameters**:  
        All parameters are shwon in **ppm** units.

.. image:: _static/fitting_ref_spec.jpg
  :scale: 60%

The fitted reference spectrum will be automatically displayed on the resulting graph. This plots will show [i] the experimental data as dots [ii] the best fit 
as red a curve and [iii] the initial values used in the minimzation in green. This is supplemented with the residum plot below. 

.. note:: **Parameters**:  
        In the case of evident mismatch between the data and the best fit, you can adjust manually adjust the initial values in the former **parameters** table ()

If the results are satisying press the the **Add current region** button to save this region and eventually to the same workflow for another region of the spectra. 
For this you will need to go back to the top of page and select **add new region** in the field **Select region to (re)process**. Otherwise move to next page **Fit from reference**. 


.. _Fit from reference:

.. ********************************************************************************
.. Fit from reference
.. ********************************************************************************

This page contains the wrapper that allows you to fit the desired data. 

.. image:: _static/fit_from_reference.jpg
  :scale: 60%

First select the region that needs to be fitted (**Select region**). Automatically MultiNMRFit will display the list of **Signal IDs** present in the selected region
along with the **processed spectra** already analyzed (e.g in the first run this nunmber will correspond to the number of the reference spectrum)

MultiNMRFit will give the choice of the spectra you want to process, By default it shows the complete dataset (here 1-256 as the pseudo2D contains 256 in the example).
However if you want to analyze the first ten spectra one can write 1-10 and it will update the list **spectra to process** automatically. Click the **Fit selected spectra**
to run the fitting of the selected spectra. The progress of the fitting will be displayed by a progress bar and once complete a message **All spectra have been fitted** will appear.

.. note:: **Fitting**:  
        This procedure can be repeated for the different regions defined in the previous pages upon selection in **Select region**.
        By default MultiNMRFit do not reprocess spectra that have been already been fitted so clicked the option if necessary.
        The reference spectrum associated with the slected region can be visualized on this page. 

Once you have fitted all the data you can move to last page 

.. _Results visualisation:

.. ********************************************************************************
.. Results visualisation
.. ********************************************************************************

This page provides several visualization options of the results. On top, you can inspect every fitted spectrum. 
If multiple signals were fitted on the the same region, you can observe individual ones by clicking on the different 
signal IDs in the figure caption.

..  _`Spectra visualisation`:

Spectra visualisation
================================================================================

Users can select the spectrum and the region to display. 

.. image:: _static/visu_spectra.jpg
  :scale: 60%

..  _`Parameters visualisation`:

Parameters visualisation
================================================================================

For the corresponding spectra shown above users can find the table of paramters. 
A particular attention must me given to the **opt** that contains the optimal values of the 
fitting routine. If one value is highlited in red it means that is value is stuck to either 
the lower or higher bound. If this the case the spectra need to re-analyzed in leaving more freedom tho the parameter.  

.. image:: _static/visu_parameters.jpg
  :scale: 60%

Finally, users can observe the variation of a given paramters as function of spectra IDs. 

.. image:: _static/visu_param_plot.jpg
  :scale: 60%

Export results
================================================================================

Users can export their results tabulated text file in 2 different manners: **all data** or **specific data**
In the first case (**all data**) all the parameters of all the regions and spectra will be saved in the **output** location 
defined in the first page of the interface. If the second case (option **specific data** selected), you can select one region, one parameter that will 
exclusively saved in the file.  


Warning and error messages
--------------------------------------------------------------------------------

Error messages are explicit. You should examine carefully any warning/error message.
After correcting the problem, you might have to restart MultiNMRFit (to reload files)
and perform the analysis again.
