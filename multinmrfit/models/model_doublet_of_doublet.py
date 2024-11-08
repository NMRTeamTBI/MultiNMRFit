"""
Model of triplet.
"""
from __future__ import annotations

import numpy as np

from multinmrfit.models.base_model import Model


class SignalModel(Model):

    def __init__(self):

        self.name = "doublet of doublet"
        self.description = "mixed gaussian-lorentzian doublet of doublet (1:1:1:1)"
        self.peak_number = 4
        self.default_params = {'model': [self.name]*6,
                               'par': ['x0', 'J1', 'J2', 'intensity', 'lw', 'gl'],
                               'ini': [1.0, 0.05, 0.02, 1e6, 0.001, 0.5],
                               'lb': [0.0, 0.01, 0.005, 1, 0.0001, 0.0],
                               'ub': [10.0, 1.0, 1.0, 1e15, 0.03, 1.0],
                               'shift_allowed': [0.01, 0.10, 0.10, 10, 0.3, 10],
                               'relative': [False, True, True, True, True, False]}

    def pplist2signal(self, peak_list):
        
        detected_peak_position = np.mean(peak_list.ppm.values)
        detected_peak_intensity = np.mean(peak_list.intensity.values)

        ll = peak_list['ppm'].tolist()
        ll.sort()
        detected_coupling_constant_J1 = np.abs(ll[2]-ll[0])
        detected_coupling_constant_J2 = np.abs(ll[1]-ll[0])

        signal = {
            "model": self.name,
            'par': {'x0': {'ini': detected_peak_position, 'lb': detected_peak_position-0.2, 'ub': detected_peak_position+0.2},
                    'intensity': {'ini': detected_peak_intensity, 'ub': 1.3*detected_peak_intensity},
                    'J1': {'ini': detected_coupling_constant_J1, 'lb': 0.8*detected_coupling_constant_J1, 'ub': 1.2*detected_coupling_constant_J1},
                    'J2': {'ini': detected_coupling_constant_J2, 'lb': 0.8*detected_coupling_constant_J2, 'ub': 1.2*detected_coupling_constant_J2}
                    }
        }

        return signal

    @staticmethod
    def simulate(params: list, ppm: list):

        sum_J1_J2 = (params[1] + params[2])/2
        dif_J1_J2 = (params[1] - params[2])/2
        dif_ppm_x0 = ppm - params[0]
        peak_1 = params[5] * params[3] / (1 + ((dif_ppm_x0 + sum_J1_J2)/params[4])**2) + (1-params[5]) * \
            params[3] * np.exp(-(dif_ppm_x0 + sum_J1_J2)**2/(2*params[4]**2))
        peak_2 = params[5] * params[3] / (1 + ((dif_ppm_x0 - sum_J1_J2)/params[4])**2) + (1-params[5]) * \
            params[3] * np.exp(-(dif_ppm_x0 - sum_J1_J2)**2/(2*params[4]**2))
        peak_3 = params[5] * params[3] / (1 + ((dif_ppm_x0 + dif_J1_J2)/params[4])**2) + (1-params[5]) * \
            params[3] * np.exp(-(dif_ppm_x0 + dif_J1_J2)**2/(2*params[4]**2))
        peak_4 = params[5] * params[3] / (1 + ((dif_ppm_x0 - dif_J1_J2)/params[4])**2) + (1-params[5]) * \
            params[3] * np.exp(-(dif_ppm_x0 - dif_J1_J2)**2/(2*params[4]**2))

        return peak_1 + peak_2 + peak_3 + peak_4
