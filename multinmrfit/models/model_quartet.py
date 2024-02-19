"""
Model of triplet.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from multinmrfit.models.base_model import Model

class SignalModel(Model):

    def __init__(self):

        self.name = "quartet"
        self.description = "mixed gaussian-lorentzian quartet (1:3:3:1)"
        self.peak_number = 4
        default_params = {'model' : [self.name]*5,
                          'par' : ['x0', 'J', 'intensity', 'lw', 'gl'],
                          'ini' : [1.0, 0.05, 1e6, 0.001, 0.5],
                          'lb' : [0.0, 0.01, 1, 0.0001, 0.0],
                          'ub' : [10.0, 1.0, 1e15, 0.03, 1.0]}
        self._params = pd.DataFrame(default_params)

    def pplist2signal(self, peak_list):
        detected_peak_position = np.mean(peak_list.ppm.values)
        detected_peak_intensity = np.mean(peak_list.intensity.values)
        detected_coupling_constant = np.abs(max(peak_list.ppm.values)-min(peak_list.ppm.values))/3

        signal = {
            "model":self.name ,
            'par':{'x0':{'ini':detected_peak_position,'lb':detected_peak_position-0.2,'ub':detected_peak_position+0.2},
                  'intensity':{'ini':detected_peak_intensity,'ub':1.3*detected_peak_intensity} ,
                   'J':{'ini':detected_coupling_constant,'lb':0.8*detected_coupling_constant,'ub':1.2*detected_coupling_constant} ,    
                          }
            }
        # add lw
        return signal


    @staticmethod
    def simulate(params: list, ppm: list):

        peak_1 = params[4] * params[2]  / ( 1 + (( ppm - params[0] - (3/2)*params[1])/params[3])**2) + (1-params[4])*params[2]*np.exp(-(ppm - params[0] - (3/2)*params[1])**2/(2*params[3]**2))
        peak_2 = params[4] * 3 * params[2]  / ( 1 + (( ppm - params[0] - (1/2)*params[1])/params[3])**2) + (1-params[4])*2*params[2]*np.exp(-(ppm - params[0]- (1/2)*params[1])**2/(2*params[3]**2))
        peak_3 = params[4] * 3 * params[2]  / ( 1 + (( ppm - params[0] + (1/2)*params[1])/params[3])**2) + (1-params[4])*2*params[2]*np.exp(-(ppm - params[0]+ (1/2)*params[1])**2/(2*params[3]**2))
        peak_4 = params[4] * params[2]  / ( 1 + (( ppm - params[0] + (3/2)*params[1])/params[3])**2) + (1-params[4])*params[2]*np.exp(-(ppm - params[0] + (3/2)*params[1])**2/(2*params[3]**2))

        return peak_1 + peak_2 + peak_3 + peak_4

