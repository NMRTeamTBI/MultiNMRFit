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
                          'ini' : [1.0, 1e6, 0.001, 0.5],
                          'lb' : [0.0, 1, 0.0001, 0.0],
                          'ub' : [10.0, 1e15, 0.03, 1.0]}
        self._params = pd.DataFrame(default_params)


    def pplist2signal(self, peak_list):
        detected_peak_position = peak_list.ppm.values[0]
        detected_peak_intensity = peak_list.intensity.values[0]

        signal = {
            "model":self.name ,
            'par':{'x0':{'ini':detected_peak_position,'lb':detected_peak_position-1,'ub':detected_peak_position+1},
                  'intensity':{'ini':detected_peak_intensity,'ub':1.1*detected_peak_intensity}       
                          }
            }
        # add lw
        return signal


    @staticmethod
    def simulate(params: list, ppm: list):

        peak_1 = params[3] * params[1]  / (1 + ((ppm - params[0])/params[2])**2) + (1-params[3]) * params[1] * np.exp(-(ppm - params[0] )**2/(2*params[2]**2))

        return peak_1


