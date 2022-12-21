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

    def __init__(self, data, signals={}, models={}, offset={}):

        logger.debug("create Spectrum object")

        # initialize data
        self.ppm = data.ppm
        self.intensity = data.intensity
        self.offset = True if len(offset) else False
        self.sim_intensity = None
        self.fit_intensity = None
        self.fit_results = None

        # initialize models
        self._initialize_models(signals, models, offset)

        # simulate from initial values
        self.sim_intensity = self.simulate(self.params['ini'].values.tolist())


    def _initialize_models(self, signals, available_models, offset):

        self.models = {}
        self.params = pd.DataFrame(columns = ['signal_id', 'model', 'par', 'ini', 'lb', 'ub'])

        # for each signal
        for id, signal in signals.items():

            logger.debug("build Model for signal '{}'".format(id))

            # create a corresponding Model object
            self.models[id] = available_models[signal['model']]()

            # update parameters values & bounds
            try:
                for par, val in signal.get("par", {}).items():
                    for k, v in val.items():
                        #logger.debug("update parameter {} - {} to {}".format(par, k, v))
                        self.models[id].set_params(par, (k, v))
            except:
                raise ValueError("error when initializing parameter '{} - {}' at value '{}'".format(par, k, v))
            
            _params = self.models[id].get_params()

            # add id
            _params.insert(0, 'signal_id', [id]*len(_params.index))

            # add global parameters indices to model
            self.models[id]._par_idx = [i for i in range(len(self.params), len(_params)+len(self.params))]
            self.params = pd.concat([self.params, _params])
        
        # add offset
        if self.offset:
            self.params.loc[len(self.params.index)] = ['full_spectrum', None, 'offset', offset.get('ini', 0), offset.get('lb', -1e6), offset.get('ub', 1e6)]

        # reset index
        self.params.reset_index(inplace=True, drop=True)

        logger.debug("parameters\n{}".format(self.params))


    @staticmethod
    def _simulate(params, ppm, models, offset=False):

        # initialize spectrum
        if offset:
            simulated_spectrum = np.empty(len(ppm))
            simulated_spectrum.fill(params[-1])
        else:
            simulated_spectrum = np.zeros(len(ppm))

        # add subspectrum of each signal
        for model in models.values():
            simulated_spectrum += model.simulate([params[i] for i in model._par_idx], ppm)

        return simulated_spectrum


    @staticmethod
    def _calculate_cost(params, func, models, ppm, intensity, offset=False):
        """
        Calculate the cost (residuum) as the sum of squared differences
        between experimental and simulated data
        """

        # simulate spectrum
        simulated_spectrum = func(params, ppm, models, offset=offset)

        # calculate sum of squared residuals
        residuum = np.sum(np.square(simulated_spectrum - intensity))

        return residuum


    def simulate(self, params):

        # simulate spectrum
        simulated_spectra = self._simulate(params, self.ppm, self.models, offset=self.offset)

        return simulated_spectra


    def integrate(self, params, bounds=[-100.0, 300.0]):

        # simulate spectrum
        from_to = np.arange(bounds[0], bounds[1], (bounds[1] - bounds[0])/4000000.0)
        area = {}
        for name, model in self.models.items():
            area[name] = model.integrate([params[i] for i in model._par_idx], from_to)

        return area


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

        # scale data
        data_scaled = self.intensity / scaling_factor

        # fit spectrum
        if method == "differential_evolution":
            self.fit_results = differential_evolution(
                Spectrum._calculate_cost, bounds=bounds,
                args=(self._simulate, self.models, self.ppm, data_scaled, self.offset),
                polish=True,
                x0=x0
            )
        elif method == "L-BFGS-B":
            self.fit_results = minimize(
                Spectrum._calculate_cost, x0=x0,
                args=(self._simulate, self.models, self.ppm, data_scaled, self.offset),
                method="L-BFGS-B",
                bounds=bounds,
                options={'maxcor': 30}
            )
        else:
            raise ValueError("optimization method '{}' not implemented".format(method))
        
        # scale back intensities and save best parameters
        self.params['opt'] = self.fit_results.x
        self.params.loc[self.params['par'].isin(["intensity", "offset"]), ["opt"]] *= scaling_factor

        # simulate spectrum from estimated parameters
        self.fit_intensity = self.simulate(self.params['opt'].values.tolist())

        # integrate spectrum
        integrals = self.integrate(self.params['opt'].values.tolist())
        self.params['integral'] = [integrals[i] if i != 'full_spectrum' else np.nan for i in self.params['signal_id'].values]

        logger.debug("parameters\n{}".format(self.params))


    def plot(self, exp=True, sim=True):
        logger.debug("create plot")
        
        # generate individual plots
        if sim:
            fig_sim = px.line(x=self.ppm, y=self.fit_intensity)
            fig_sim.update_traces(line_color='red')
        if exp:
            fig_meas = px.scatter(x=self.ppm, y=self.intensity)

        # combine plots
        if sim and exp:
            fig = go.Figure(data=fig_meas.data + fig_sim.data)
        elif exp:
            fig = go.Figure(data=fig_meas.data)
        elif sim:
            fig = go.Figure(data=fig_sim.data)
        
        return fig