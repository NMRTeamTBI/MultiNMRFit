"""
Model of singlet.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from multinmrfit.models.base_model import Model

class SignalModel(Model):

    def __init__(self):

        self.name = "singlet"
        self.description = "mixed gaussian-lorentzian singlet"
        self.peak_number = 1
        default_params = {'model' : [self.name]*4,
                          'par' : ['x0', 'intensity', 'lw', 'gl'],
                          'ini' : [1.0, 1e6, 0.01, 0.5],
                          'lb' : [0.0, 1, 0.001, 0.0],
                          'ub' : [10.0, 1e15, 0.03, 1.0]}
        self._params = pd.DataFrame(default_params)

    @staticmethod
    def simulate(params: list, ppm: list):

        peak_1 = params[3] * params[1]  / (1 + ((ppm - params[0])/params[2])**2) + (1-params[3]) * params[1] * np.exp(-(ppm - params[0] )**2/(2*params[2]**2))

        return peak_1

    # def pplist2signal(self,peak_list):
