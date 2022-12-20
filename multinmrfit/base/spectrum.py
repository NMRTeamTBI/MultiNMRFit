"""
multinmrfit main module
"""

import logging
import numpy as np
import pandas as pd
from scipy.optimize import minimize, differential_evolution
import plotly.express as px
import plotly.graph_objects as go


# create logger
logger = logging.getLogger(__name__)


class Spectrum(object):
    """
    This class is responsible for most of multinmrfit heavy work. Features included are:

        * **models initialization**
        * **spectrum simulation**
        * **spectrum fitting** using `scipy.optimize.minimize ('Differential evolution', with polish with 'L-BFGS-B' method) <https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html#optimize-minimize-lbfgsb>`_
        * **sensitivity analysis, khi2 tests and plotting**

    :param data: DataFrame containing data and passed by IOstream object
    :type data: class: pandas.DataFrame
    :param model: Model to initialize parameters and optimize
    :type model: physiofit.models.base_model.Model
    :param mc: Should Monte-Carlo sensitivity analysis be performed (default=True)
    :type mc: Boolean
    :param iterations: number of iterations for Monte-Carlo simulation (default=100)
    :type iterations: int
    """

    def __init__(self, data, signals={}, models={}, offset=False):

        logger.debug("create spectrum")

        self.ppm = data.ppm
        self.intensity = data.intensity
        self.offset = offset
        self.intensity_fit = None
        self.fit_results = None

        # initialize models
        self._initialize_models(signals, models)


    def _initialize_models(self, signals, available_models):

        self.models = {}
        self.params = pd.DataFrame(columns = ['signal_id', 'model', 'par', 'ini', 'lb', 'ub'])

        # for each signal
        for id, signal in signals.items():

            logger.debug("build model for signal '{}'".format(id))

            # add the corresponding model
            self.models[id] = available_models[signal['model']]()

            # update parameters values & bounds
            for par, val in signal.get("par", {}).items():
                for k, v in val.items():
                    #logger.debug("update parameter {}.{} to {}".format(par, k, v))
                    self.models[id].set_params(par, (k, v))
            _params = self.models[id].get_params()

            # add id
            _params.insert(0, 'signal_id', [id]*len(_params))

            # add global parameters indices to model
            self.models[id]._par_idx = [i for i in range(len(self.params), len(_params)+len(self.params))]
            self.params = pd.concat([self.params, _params])
        
        # add offset
        if self.offset:
            self.params.loc[len(self.params.index)] = ['full_spectra', None, 'offset', 0, -1e6, 1e6]

        # reset index
        self.params.reset_index(inplace=True, drop=True)

        logger.debug("parameters\n{}".format(self.params))


    @staticmethod
    def _simulate(params, ppm, models, scaling_factor=1, offset=False):

        # initialize spectrum at 0
        simulated_spectra = np.zeros(len(ppm))

        # add subspectrum of each signal
        for model in models.values():
            simulated_spectra += model.simulate([params[i] for i in model._par_idx], ppm)

        # add offset
        if offset:
            simulated_spectra += params[-1]
        
        # apply scaling factor
        simulated_spectra *= scaling_factor
        
        return simulated_spectra


    @staticmethod
    def _calculate_cost(params, func, models, ppm, intensity, scaling_factor, offset=False):
        """
        Calculate the cost (residuum) as the sum of squared differences
        between experimental and simulated data
        """

        # simulate spectrum
        simulated_spectrum = func(params, ppm, models, scaling_factor=scaling_factor, offset=offset)

        # calculate sum of squared residuals
        residuum = np.sum(np.square(simulated_spectrum - intensity))

        return residuum


    def simulate(self, params):

        # simulate spectrum
        simulated_spectra = self._simulate(params, self.ppm, self.models, offset=self.offset)

        return simulated_spectra


    def fit(self, method="L-BFGS-B"):
        """
        Run the optimization on input parameters using the cost function and
        Scipy minimize (L-BFGS-B method that is deterministic and uses the
        gradient method for optimizing)
        """

        logger.debug("fit spectrum")
        
        # set scaling factor to stabilize convergence
        scaling_factor = np.mean(self.intensity)

        # apply scaling factor on intensities
        params_scaled = self.params.copy(deep=True)
        params_scaled.loc[params_scaled['par'].isin(["intensity", "offset"]), ["ini", "lb", "ub"]] /= scaling_factor
        
        # set initial values
        x0 = params_scaled['ini'].values.tolist()

        # set bounds
        bounds = list(zip(params_scaled['lb'], params_scaled['ub']))

        # fit spectrum
        if method == "differential_evolution":
            self.fit_results = differential_evolution(
                Spectrum._calculate_cost, bounds=bounds,
                args=(self._simulate, self.models, self.ppm, self.intensity, scaling_factor, self.offset),
                polish=True,
                x0=x0
            )
        elif method == "L-BFGS-B":
            self.fit_results = minimize(
                Spectrum._calculate_cost, x0=x0,
                args=(self._simulate, self.models, self.ppm, self.intensity, scaling_factor, self.offset),
                method="L-BFGS-B",
                bounds=bounds,
                options={'maxcor': 30}
            )
        else:
            raise ValueError("optimization method '{}' not implemented".format(method))
        
        # scale back intensities
        self.params['opt'] = self.fit_results.x
        self.params.loc[self.params['par'].isin(["intensity", "offset"]), ["opt"]] *= scaling_factor
        logger.debug("parameters\n{}".format(self.params))

        # simulate spectrum from estimated parameters
        self.intensity_fit = self.simulate(self.params['opt'].values.tolist())


    def plot(self):
        logger.debug("create plot")
        fig_sim = px.line(x=self.ppm, y=self.intensity_fit)
        fig_sim.update_traces(line_color='red')
        fig_meas = px.scatter(x=self.ppm, y=self.intensity)
        fig = go.Figure(data=fig_meas.data + fig_sim.data)
        fig.show()