"""
multinmrfit spectrum module
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
        * **spectrum fitting** using `scipy.optimize.minimize ('Differential evolution',with polish with 'L-BFGS-B' method)
          <https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html#optimize-minimize-lbfgsb>`_
        * **plotting**

    :param data: DataFrame containing data (columns 'ppm' and 'intensity')
    :type data: class: pandas.DataFrame
    :param signals: signals to fit
    :type signals: dict
    :param models: available models
    :type models: dict
    :param offset: offset
    :type offset: dict
    """

    def __init__(self, data, signals, models, offset=None):

        logger.debug("create Spectrum object")

        # initialize data
        self.ppm = data.ppm
        self.intensity = data.intensity
        self.offset = False
        self.models = {}
        self.params = pd.DataFrame(columns = ['signal_id', 'model', 'par', 'ini', 'lb', 'ub'])

        # initialize models
        self._initialize_models(signals, models)

        # update parameters
        self.set_params(signals)

        # set offset
        self.set_offset(offset=offset)


    def _initialize_models(self, signals, available_models):

        # for each signal
        for id, signal in signals.items():

            logger.debug("build Model for signal '{}'".format(id))

            # create a corresponding Model object
            self.models[id] = available_models[signal['model']]()

            # get default parameters & bounds
            _params = self.models[id].get_params()

            # add id
            _params.insert(0, 'signal_id', [id]*len(_params.index))

            # add global parameters indices to model
            self.models[id]._par_idx = [i for i in range(len(self.params), len(_params)+len(self.params))]
            self.params = pd.concat([self.params, _params])

        # reset index
        self.params.reset_index(inplace=True, drop=True)

        logger.debug("parameters\n{}".format(self.params))


    def set_params(self, signals):

        # update parameters values & bounds
        for id, signal in signals.items():
            for par, val in signal.get("par", {}).items():
                for k, v in val.items():
                    #logger.debug("update parameter {} - {} to {}".format(par, k, v))
                    self.models[id].set_params(par, (k, v))
                    # update self.params
                    self.params.at[(self.params["signal_id"] == id) & (self.params["par"] == par), k] = v                      

        
    def set_offset(self, offset):

        # update offset
        if offset is None:
            if self.offset:
                # remove line in self.params
                self.params.drop(self.params[(self.params["signal_id"] == 'full_spectrum') & (self.params["par"] == 'offset')].index, inplace=True)
                self.offset = False
        else:
            if isinstance(offset, dict):
                if self.offset:
                    for k, v in offset.items():
                        self.params.at[(self.params["signal_id"] == 'full_spectrum') & (self.params["par"] == 'offset'), k] = v
                else:
                    self.offset = True
                    default_offset = 0.2*np.max(self.intensity)
                    self.params.loc[len(self.params.index)] = ['full_spectrum', None, 'offset', offset.get('ini', 0), offset.get('lb', -default_offset), offset.get('ub', default_offset)]
            else:
                raise ValueError("offset must be a dict")


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


    def simulate(self, params=None):

        if params is None:
            params = self.params['ini'].values.tolist()

        # simulate spectrum
        simulated_spectra = self._simulate(params, self.ppm, self.models, offset=self.offset)

        return simulated_spectra


    def integrate(self, params=None, bounds=[-100.0, 300.0]):

        if params is None:
            params = self.params['ini'].values.tolist()

        # simulate spectrum
        from_to = np.arange(bounds[0], bounds[1], (bounds[1] - bounds[0])/4000000.0)
        area = {}
        for name, model in self.models.items():
            area[name] = model.integrate([params[i] for i in model._par_idx], from_to)

        return area


    def check_parameters(self):

        test_bounds = (self.params['ini'] < self.params['lb']) | (self.params['ini'] > self.params['ub'])
        if any(test_bounds):
            par_error = self.params.loc[test_bounds, 'par'].values.tolist()
            raise ValueError("initial values of parameters '{}' must be within bounds.".format(par_error))


    def fit(self, method="L-BFGS-B"):
        """
        Run the optimization on input parameters using the cost function and
        Scipy minimize (L-BFGS-B method that is deterministic and uses the
        gradient method for optimizing)
        """

        logger.debug("fit spectrum")

        # check parameters
        self.check_parameters()
        
        # set scaling factor to stabilize convergence
        scaling_factor = np.mean(self.intensity)

        # apply scaling factor on parameters (intensity & offset)
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
                Spectrum._calculate_cost,
                maxiter=700,
                popsize=10,
                bounds=bounds,
                args=(self._simulate, self.models, self.ppm, data_scaled, self.offset),
                polish=True,
                x0=x0
            )

        elif method == "L-BFGS-B":

            self.fit_results = minimize(
                Spectrum._calculate_cost,
                x0=x0,
                args=(self._simulate, self.models, self.ppm, data_scaled, self.offset),
                method="L-BFGS-B",
                bounds=bounds,
                options={'maxcor': 30}
            )

        else:

            raise ValueError("optimization method '{}' not implemented".format(method))
        
        # scale back estimated parameters
        self.params['opt'] = self.fit_results.x
        self.params.loc[self.params['par'].isin(["intensity", "offset"]), ["opt"]] *= scaling_factor

        # simulate spectrum from estimated parameters
        self.fit_intensity = self.simulate(self.params['opt'].values.tolist())

        # integrate spectrum
        integrals = self.integrate(self.params['opt'].values.tolist())
        self.params['integral'] = [integrals[i] if i != 'full_spectrum' else np.nan for i in self.params['signal_id'].values]

        logger.debug("parameters\n{}".format(self.params))


    def plot(self, exp=True, ini=True, fit=True):
        logger.debug("create plot")
        
        # generate individual plots
        data, series_names = [], []
        if exp:
            fig_exp = px.scatter(x=self.ppm, y=self.intensity)
            fig_exp.update_traces(showlegend=True)
            data += fig_exp.data
            series_names.append("measured")
        if ini:
            ini_intensity = self.simulate(params = self.params['ini'].values.tolist())
            fig_ini = px.line(x=self.ppm, y=ini_intensity)
            fig_ini.update_traces(line_color='red')
            fig_ini.update_traces(showlegend=True)
            data += fig_ini.data
            series_names.append("initial values")
        if fit:
            if 'opt' in self.params.columns:
                fit_intensity = self.simulate(params = self.params['opt'].values.tolist())
                fig_fit = px.line(x=self.ppm, y=fit_intensity)
                fig_fit.update_traces(line_color='green')
                fig_fit.update_traces(showlegend=True)
                data += fig_fit.data
                series_names.append("best fit")

        # combine plots
        fig = go.Figure(data=data)
        fig.update_yaxes(exponentformat = 'power', showexponent="last")
        fig.update_xaxes(autorange="reversed")
        fig.update_layout(xaxis_title="chemical shift (ppm)", yaxis_title="intensity")

        for idx, name in enumerate(series_names):
            fig.data[idx].name = name
            fig.data[idx].hovertemplate = name
        fig.update_layout(legend_title_text='Legend')
        
        return fig