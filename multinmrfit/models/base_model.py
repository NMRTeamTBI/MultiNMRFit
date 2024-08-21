from __future__ import annotations

import numpy as np
import pandas as pd


class Model(object):

    def __init__(self):

        self.name = None
        self.description = None
        self._params = None
        self._cnstr_wd = None
        self._par_idx = None
        self.peak_number = None

    def set_default_params(self):
        self._params = pd.DataFrame(dict((k, self.default_params[k]) for k in ('model', 'par', 'ini', 'lb', 'ub')))
        return self._params

    def set_default_cnstr_wd(self):
        self._cnstr_wd = pd.DataFrame(dict((k, self.default_params[k]) for k in ('model', 'par', 'shift_allowed', 'relative')))
        return self._cnstr_wd

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
        integral = np.trapz(y=sim_spectra, x=ppm)
        return integral
