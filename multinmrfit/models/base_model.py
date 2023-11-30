from __future__ import annotations

import numpy as np


class Model(object):

    def __init__(self):

        self.name = None
        self.description = None
        self._params = None
        self._par_idx = None
        self.peak_number = None
    
    def get_params(self):
        return self._params

    def set_params(self, name: str, val: tuple):
        try:
            self._params.loc[self._params["par"] == name, val[0]] = val[1]
        except:
            if name not in self._params["par"].values:
                raise ValueError("parameter '{}' not found".format(name))
            if val[0] not in self._params.columns:
                raise ValueError("key '{}' not found".format(val[0]))

    def integrate(self, params: list, ppm: list):
        sim_spectra = self.simulate(params, ppm)
        integral = np.sum(sim_spectra) * np.abs(ppm[0] - ppm[1])
        return integral
    


