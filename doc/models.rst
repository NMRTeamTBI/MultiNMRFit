..  Models:

################################################################################
Models
################################################################################

Signal models for some typical multiplets (singlet, doublet, triplet, quadruplet and doublet of doublet) are included 
in multiNMRFit, and users can also build their own models.

.. note:: We would be happy to broaden the types of models shipped with multiNMRFit. If you have developed a new model, it might be 
          usefull and valuable to the fluxomics community! Please, keep in touch with us to discuss and see if we can include your 
          model in the built-in models shipped with multiNMRFit! :)

The models used in MultiNMRFit can be found in the models folder, which is located in the multinmrfit package. To 
find the path to the multinmrfit package, you can use the following command in a Python console:

.. code-block:: python

    import multinmrfit
    print(multinmrfit.__path__)

All models follow the same 
format. Have a look to `model_singlet.py <https://github.com/NMRTeamTBI/MultiNMRFit/blob/master/multinmrfit/models/model_singlet.py/>`_ as a template.

Briefly, you will need to adapt the following functions:

- **__init__**: initialize the signal model object with the following attributes:
    - **name**: the name of the model.
    - **description**: a brief description of the model.
    - **peak_number**: the number of peaks in the signal.
    - **default_params**: a list of the parameters that will be estimated by the fitting algorithm, with their default values and bounds.

- **pplist2signal**: the function that will be used to built the signal from the peak list. It should return a dictionary containing the name of the signal, and optionaly some parameter values to be updated based on the peak list (if different from the default values).

- **simulate**: the function that will be used to simulate the signal. It should return the simulated signal given the parameters and chemical shifts.

Once you have developed a new model, you can add it to the models folder. The new model will be automatically detected by MultiNMRFit.

.. note:: The file name must start with "model_".

Users can add additionnal custom models following this format. We'll provide additional information 
on the construction of new models soon! In the meantime, do not hesitate to grab us a message or 
open an issue in our GitHub repository, we will be happy to help! 