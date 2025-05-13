..  Models:

################################################################################
Models
################################################################################

Models shipped with multiNMRFit
******************************

Signal models for some typical multiplets (mixed Gaussian-Lorentzian models of singlet, doublet, triplet, quadruplet and doublet of doublet) are included 
in multiNMRFit.

The models used in MultiNMRFit can be found in the models folder, which is located in the multinmrfit package. To 
find the path to the multinmrfit package, you can use the following command in a Python console:

.. code-block:: python

    import multinmrfit
    print(multinmrfit.__path__)

All models follow the same 
format. Have a look to `model_singlet.py <https://github.com/NMRTeamTBI/MultiNMRFit/blob/master/multinmrfit/models/model_singlet.py/>`_ for a detailed example.

User-made models
*****************

Overview
--------

multiNMRFit is designed to be easily extended with new signal models. Users can create their own signal models and add them to the list of available models.

This section explains how to write a model and how to implement it
on your multiNMRFit instance. All models follow the same 
format, have a look to `model_singlet.py <https://github.com/NMRTeamTBI/MultiNMRFit/blob/master/multinmrfit/models/model_singlet.py/>`_ as an example.


Build a template
----------------

To implement user-made models, multiNMRFit leverages Python's object model to create classes that inherit from an Abstract
Base Class and that handles all the heavy-lifting for implementation. A simple set of rules enables
users to use their model in multiNMRFit.

The model must be a class located in a dedicated module. Start by opening a text file
using your IDE (Integrated Development Environment), and enter the following structure in the file::

.. code-block:: python

    import numpy as np
    from multinmrfit.models.base_model import Model

    class SignalModel(Model):

        def __init__(self, data):
            self.name = "model name"
            self.description = "model description"
            self.peak_number = int
            self.default_params = {}

        def pplist2signal(self, peak_list):
            pass

        @staticmethod
        def simulate():
            pass

    if __name__ == "__main__":
        pass

This is the base template to build your model, which includes the following methods:

- **__init__**: initialize the signal model object. 

- **pplist2signal**: the function that will be used to built the signal from the peak list. It should return a dictionary containing the name of the signal, and optionaly some parameter values to be updated based on the peak list (if different from the default values).

- **simulate**: the function that will be used to simulate the signal. It should return the simulated signal given the parameters and chemical shifts.

Additional methods are allowed if needed (e.g. to carry out intermediary steps for the simulation).

Populate the template
---------------------

The first attribute to add in your model's :samp:`__init__` method is the model name.

This method should include the following attributes:

  - **name**: the name of the model. It should be unique and descriptive.
  - **description**: a short description of the model.
  - **peak_number**: the number of peaks in the model. This is used to determine how many peaks are contained in the signal.
  - **default_params**: a dictionary containing the default parameters for the model. The keys should be the names of the parameters, and the values should be their default values. The parameters are defined as follows:
    - **model**: name of the model
    - **par**: name of the parameters
    - **ini**: default value of the parameter
    - **lb**: lower bound of the parameter
    - **ub**: upper bound of the parameter
    - **shift_allowed**: window of allowed shift for the parameter in comparison to the previous spectrum used as reference. This is used to dynamically adapt the bounds from a spectrum to the next one during the fitting process in batch.
    - **relative**: boolean indicating if the shift allowed is expressed as a relative or absolute value. If True, the shift is relative to the parameter value. If False, the shift is defined as absolute value.

For instance, in the case of a mixed Gaussian-Lorentzian doublet model, the default parameters are:

.. code-block:: python

    import numpy as np
    from multinmrfit.models.base_model import Model

    class SignalModel(Model):

        def __init__(self):
            self.name = "doublet"
            self.description = "mixed gaussian-lorentzian doublet"
            self.peak_number = 2
            self.default_params = {'model': [self.name]*5,
                                   'par': ['x0', 'J', 'intensity', 'lw', 'gl'],
                                   'ini': [1.0, 0.05, 1e6, 0.001, 0.5],
                                   'lb': [0.0, 0.01, 1, 0.0001, 0.0],
                                   'ub': [10.0, 1.0, 1e15, 0.03, 1.0],
                                   'shift_allowed': [0.01, 0.10, 10, 0.3, 10],
                                   'relative': [False, True, True, True, False]}

        def pplist2signal(self, peak_list):
            pass

        @staticmethod
        def simulate(params, ppm):
            pass

    if __name__ == "__main__":
        pass

The second method to implement is the :samp:`pplist2signal` method. This method is used to convert a peak list into a signal. It should return a dictionary containing the name of the signal, and optionaly some parameter values to be updated based on the peak list (if different from the default values). The dictionary should contain the following keys:

  - **model**: name of the signal model
  - **par**: dictionary containing the parameters of the signal. The keys should be the names of the parameters, and the values should be a dictionary containing their values and lower and upper bounds.

For instance, in the case of a mixed Gaussian-Lorentzian doublet model, the signal is built as follows:

.. code-block:: python

    import numpy as np
    from multinmrfit.models.base_model import Model

    class SignalModel(Model):

        def __init__(self):
            self.name = "doublet"
            self.description = "mixed gaussian-lorentzian doublet"
            self.peak_number = 2
            self.default_params = {'model': [self.name]*5,
                                   'par': ['x0', 'J', 'intensity', 'lw', 'gl'],
                                   'ini': [1.0, 0.05, 1e6, 0.001, 0.5],
                                   'lb': [0.0, 0.01, 1, 0.0001, 0.0],
                                   'ub': [10.0, 1.0, 1e15, 0.03, 1.0],
                                   'shift_allowed': [0.01, 0.10, 10, 0.3, 10],
                                   'relative': [False, True, True, True, False]}

        def pplist2signal(self, peak_list):
            detected_peak_position = np.mean(peak_list.ppm.values)
            detected_peak_intensity = peak_list.intensity.values[0]
            detected_coupling_constant = np.abs(max(peak_list.ppm.values)-min(peak_list.ppm.values))

            signal = {
                "model": self.name,
                'par': {'x0': {'ini': detected_peak_position, 'lb': detected_peak_position-1, 'ub': detected_peak_position+1},
                        'intensity': {'ini': detected_peak_intensity, 'ub': 1.1*detected_peak_intensity},
                        'J': {'ini': detected_coupling_constant, 'lb': 0.8*detected_coupling_constant, 'ub': 1.2*detected_coupling_constant},
                        }
            }
            
        return signal

        @staticmethod
        def simulate(params, ppm):
            pass

    if __name__ == "__main__":
        pass

Finally, the last method to implement is the :samp:`simulate` method. This method is used to simulate the signal. It should return the simulated signal given the parameters and chemical shifts. The method should take as input the parameters and chemical shifts, and return the simulated signal.

.. code-block:: python

    import numpy as np
    from multinmrfit.models.base_model import Model

    class SignalModel(Model):

        def __init__(self):
            self.name = "doublet"
            self.description = "mixed gaussian-lorentzian doublet"
            self.peak_number = 2
            self.default_params = {'model': [self.name]*5,
                                   'par': ['x0', 'J', 'intensity', 'lw', 'gl'],
                                   'ini': [1.0, 0.05, 1e6, 0.001, 0.5],
                                   'lb': [0.0, 0.01, 1, 0.0001, 0.0],
                                   'ub': [10.0, 1.0, 1e15, 0.03, 1.0],
                                   'shift_allowed': [0.01, 0.10, 10, 0.3, 10],
                                   'relative': [False, True, True, True, False]}

        def pplist2signal(self, peak_list):
            detected_peak_position = np.mean(peak_list.ppm.values)
            detected_peak_intensity = peak_list.intensity.values[0]
            detected_coupling_constant = np.abs(max(peak_list.ppm.values)-min(peak_list.ppm.values))

            signal = {
                "model": self.name,
                'par': {'x0': {'ini': detected_peak_position, 'lb': detected_peak_position-1, 'ub': detected_peak_position+1},
                        'intensity': {'ini': detected_peak_intensity, 'ub': 1.1*detected_peak_intensity},
                        'J': {'ini': detected_coupling_constant, 'lb': 0.8*detected_coupling_constant, 'ub': 1.2*detected_coupling_constant},
                        }
            }
            
        return signal

        @staticmethod
        def simulate(params, ppm):
            peak_1 = params[4] * params[2] / (1 + ((ppm - params[0] - (params[1]/2))/params[3])**2) + (1-params[4]) * \
                params[2]*np.exp(-(ppm - params[0] - (params[1]/2))**2/(2*params[3]**2))
            peak_2 = params[4] * params[2] / (1 + ((ppm - params[0] + (params[1]/2))/params[3])**2) + (1-params[4]) * \
                params[2]*np.exp(-(ppm - params[0] + (params[1]/2))**2/(2*params[3]**2))

        return peak_1 + peak_2

    if __name__ == "__main__":
        pass


Test the model
---------------------

We can now check that the model can be initialized properly. Use the block at the end of the file for
testing purposes. Here is an example of how you can test the model:

.. code-block:: python

    if __name__ == "__main__":

        model = SignalModel()
        print(model.name)
        print(model.description)
        print(model.peak_number)
        print(model.default_params)

If you now run the file, you should have a standard output in your console that contains the name of the model, its description, the number of peaks and the default parameters. If you have an error message, check the code and correct it.

The last step is to simulate a spectra with your model. This can be done using the following code:

.. code-block:: python

    if __name__ == "__main__":

        model = SignalModel()
        x_ppm = np.arange(0.0, 10.0, 0.01)
        spectrum = model.simulate(model.default_params, x_ppm)
        print(spectrum)

If you now run the file, you should have a standard output in your console that contains the simulated intensities. If you have an error message, check the code and correct it.


Include the model in multiNMRFit
---------------------

To test the integration of the model into the GUI, copy the :file:`.py` file
in the folder :file:`models` of multiNMRFit directory.

To find the path to the multinmrfit package, you can use the following command in a Python console:

.. code-block:: python

    import multinmrfit
    print(multinmrfit.__path__)

Once you have included your model, you can start multiNMRFit's GUI and use your model to fit a spectra. In case of errors, 
have a look to the error message and correct the code.

.. note:: We would be happy to broaden the types of models shipped with multiNMRFit. If you have developed a new model, it might be 
          usefull and valuable to the NMR community! Please, keep in touch with us to discuss on the model and see if we can include your 
          model in the built-in models shipped with multiNMRFit! :)