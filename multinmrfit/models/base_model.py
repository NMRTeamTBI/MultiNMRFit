from __future__ import annotations


class Model(object):

    def __init__(self):

        self.name = None
        self._params = None
        self._par_idx = None
    
    def get_params(self):
        return self._params

    def set_params(self, name: str, val: tuple):
        try:
            self._params.at[self._params["par"] == name, val[0]] = val[1]
        except:
            if name not in self._params["par"].values:
                raise ValueError("parameter '{}' not found".format(name))
            if val[0] not in self._params.columns:
                raise ValueError("key '{}' not found".format(val[0]))


