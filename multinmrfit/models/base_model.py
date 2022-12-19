from __future__ import annotations

#from abc import ABC, abstractmethod
#from ast import literal_eval

#import pandas as pd
#import numpy as np


# Initialization: nom des métabolites en entrée

# Get les parametres en fonction du modèle: retourne les noms des paramètres
# (optimisables et non),leurs valeurs initiales et les bounds pour ceux qui
# sont optimisables

# Besoin d'une fonction simulate propre au modèle qui prends les temps,
# les paramètres optimisables optimisables et non optimisables


class Model:

    def __init__(self):

        self.model_name = None
        self._params = None


    #def __repr__(self):
    #    return f"Selected model: {self.model_name}\n" \
    #           f"Parameters to estimate: {self._params}\n"

    #@ abstractmethod
    #def get_params(self):
    #    """
    #
    #    :return params_to_estimate: List of parameters to estimate
    #    :return fixed_parameters: dict of constant parameters
    #    :return bounds: dict of upper and lower bounds
    #    :return default_init_values: dict containing default initial values for
    #                                params
    #    """
    #    pass

    #@ abstractmethod
    #def set_params(self, name: str, val: tuple):
    #    """
    #
    #    :return params_to_estimate: List of parameters to estimate
    #    :return fixed_parameters: dict of constant parameters
    #    :return bounds: dict of upper and lower bounds
    #    :return default_init_values: dict containing default initial values for
    #                                params
    #    """
    #    pass
    
    
    def get_params(self):
        return self._params

    def set_params(self, name: str, val: tuple):
        self._params.at[self._params["par"] == name, val[0]] = val[1]

    @staticmethod
    def simulate(params: list, ppm: list):
        pass

