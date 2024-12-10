from __future__ import annotations  # Importing annotations from future versions of Python

import numpy as np  # Importing the numpy library for numerical operations
import pandas as pd  # Importing the pandas library for data manipulation


class Model(object):
    """
    A base class for models.

    Attributes:
        name (str): The name of the model.
        description (str): The description of the model.
        _params (pandas.DataFrame): Private variable to store the model parameters.
        _cnstr_wd (pandas.DataFrame): Private variable to store the constraint window.
        _par_idx (None): Private variable to store the parameter index.
        peak_number (None): The number of peaks in the model.
    """

    def __init__(self):
        """
        Initializes the Model object.
        """
        self.name = None
        self.description = None
        self._params = None
        self._cnstr_wd = None
        self._par_idx = None
        self.peak_number = None

    def set_default_params(self):
        """
        Sets the default parameters for the model.

        Returns:
            pandas.DataFrame: The default parameters for the model.
        """
        self._params = pd.DataFrame(dict((k, self.default_params[k]) for k in ('model', 'par', 'ini', 'lb', 'ub')))
        return self._params

    def set_default_cnstr_wd(self):
        """
        Sets the default constraint window for the model.

        Returns:
            pandas.DataFrame: The default constraint window for the model.
        """
        self._cnstr_wd = pd.DataFrame(dict((k, self.default_params[k]) for k in ('model', 'par', 'shift_allowed', 'relative')))
        return self._cnstr_wd

    def set_params(self, name: str, val: tuple):
        """
        Sets the value of a parameter for the model.

        Args:
            name (str): The name of the parameter.
            val (tuple): The (key,value) pair to set for the parameter.

        Raises:
            ValueError: If the parameter or key is not found.
        """
        try:
            self._params.loc[self._params["par"] == name, val[0]] = val[1]
        except:
            if name not in self._params["par"].values:
                raise ValueError("parameter '{}' not found".format(name))
            if val[0] not in self._params.columns:
                raise ValueError("key '{}' not found".format(val[0]))

    def integrate(self, params: list, ppm: list):
        """
        Calculates the integral of the simulated spectra.

        Args:
            params (list): The parameters for the model.
            ppm (list): The ppm values.

        Returns:
            float: The calculated integral.
        """
        sim_spectra = self.simulate(params, ppm)
        integral = np.trapz(y=sim_spectra, x=ppm)
        return integral
