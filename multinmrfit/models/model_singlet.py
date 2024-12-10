"""
Model of a singlet.
"""
from __future__ import annotations

# required libraries
import numpy as np
from multinmrfit.models.base_model import Model


class SignalModel(Model):
    """
    A class representing a signal model for a mixed gaussian-lorentzian singlet.

    Attributes:
        name (str): The name of the signal model.
        description (str): A description of the signal model.
        peak_number (int): The number of peaks in the signal model.
        default_params (dict): A dictionary containing the default parameters for the signal model.

    Methods:
        pplist2signal(peak_list): Set parameters from a peaklist.
        simulate(params, ppm): Simulate a singlet peak from a set of parameters at given chemical shifts.
    """

    def __init__(self):
        """
        Initialize the model object, with the name, description, number of peaks and default parameters.
        """

        # name of the model
        self.name = "singlet"
        # description of the model
        self.description = "mixed gaussian-lorentzian singlet"
        # number of peaks in the model
        self.peak_number = 1
        # names of the parameters, and defaults for initial values, lower and 
        # upper bounds, shift allowed and relative/absolute changes
        self.default_params = {'model': [self.name]*4,
                               'par': ['x0', 'intensity', 'lw', 'gl'],
                               'ini': [1.0, 1e6, 0.001, 0.5],
                               'lb': [0.0, 1, 0.0001, 0.0],
                               'ub': [10.0, 1e15, 0.03, 1.0],
                               'shift_allowed': [0.01, 10, 0.3, 10],
                               'relative': [False, True, True, False]}

    def pplist2signal(self, peak_list):
        """
        Set parameters from a peaklist (initial values, and bounds).

        Args:
            peak_list (DataFrame): A DataFrame containing the peak list.

        Returns:
            dict: A dictionary containing the initial values and bounds of the parameters.
        """

        # get the detected chemical shift and intensity
        detected_peak_position = peak_list.ppm.values[0]
        detected_peak_intensity = peak_list.intensity.values[0]

        # create a dictionary containing the initial values and bounds on some parameters,
        # which are calculated from the chemical shift and intensity
        signal = {
            'model': self.name,
            'par': {
                'x0': {'ini': detected_peak_position, 'lb': detected_peak_position-1, 'ub': detected_peak_position+1},
                'intensity': {'ini': detected_peak_intensity, 'ub': 1.1*detected_peak_intensity}
                }
        }

        return signal

    @staticmethod
    def simulate(params: list, ppm: list):
        """
        Simulate a singlet peak from a set of parameters at given chemical shifts.

        Args:
            params (list): A list of parameters for the singlet peak.
            ppm (list): A list of chemical shifts at which to simulate the peak.

        Returns:
            1darray: A 1darray containing the simulated singlet peak.
        """

        # mixed gaussian-lorentzian function of a singlet
        peak_1 = params[3] * params[1] / (1 + ((ppm - params[0])/params[2])**2) + (1-params[3]) * params[1] * np.exp(-(ppm - params[0])**2/(2*params[2]**2))

        return peak_1
