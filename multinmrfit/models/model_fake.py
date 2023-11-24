"""
Model of doublet.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from multinmrfit.models.base_model import Model

class SignalModel(Model):

    def __init__(self):

        self.name = "fake"
        self.description = "mixed gaussian-lorentzian doublet"
        self.peak_number = 2
        default_params = {'model' : [self.name]*5,
                          'par' : ['x0', 'J', 'intensity', 'lw', 'gl'],
                          'ini' : [1.0, 0.05, 1e6, 0.01, 0.5],
                          'lb' : [0.0, 0.01, 1, 0.001, 0.0],
                          'ub' : [10.0, 1.0, 1e15, 0.03, 1.0]}
        self._params = pd.DataFrame(default_params)

    @staticmethod
    def simulate(params: list, ppm: list):

        peak_1 = params[4] * params[2]  / ( 1 + (( ppm - params[0] - (params[1]/2))/params[3])**2) + (1-params[4])*params[2]*np.exp(-(ppm - params[0] - (params[1]/2))**2/(2*params[3]**2))
        peak_2 = params[4] * params[2]  / ( 1 + (( ppm - params[0] + (params[1]/2))/params[3])**2) + (1-params[4])*params[2]*np.exp(-(ppm - params[0] + (params[1]/2))**2/(2*params[3]**2))

        return peak_1 + peak_2

