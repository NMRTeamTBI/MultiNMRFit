"""
Module containing the methods used by PhysioFit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from multinmrfit.models.base_model import Model

class Singlet(Model):

    def __init__(self):

        #super().__init__()
        self.model_name = "singlet"
        default_params = {'model' : ["singlet"]*4,
                          'par' : ['x0', 'intensity', 'lw', 'gl'],
                          'ini' : [1.0, 1e6, 0.001, 0.5],
                          'lb' : [0.0, 1, 0.01, 0.0],
                          'ub' : [10.0, 1e15, 0.03, 1.0]}
        self._params = pd.DataFrame(default_params)

    @staticmethod
    def simulate(params: list, ppm: list):

        #x0 = params[0]
        #h_s = params[1]
        #lw = params[2]
        #a = params[3]
        #signal = a * h_s  / (1 + ((ppm - x0)/lw)**2) + (1-a) * h_s * np.exp(-(ppm - x0 )**2/(2*lw**2))

        signal = params[3] * params[1]  / (1 + ((ppm - params[0])/params[2])**2) + (1-params[3]) * params[1] * np.exp(-(ppm - params[0] )**2/(2*params[2]**2))

        return signal

