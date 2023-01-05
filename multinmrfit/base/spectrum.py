"""
multinmrfit spectrum module
"""

import logging
import numpy as np
import pandas as pd
import nmrglue as ng
from scipy.optimize import minimize, differential_evolution
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import multinmrfit.base.io as io


# create logger
logger = logging.getLogger(__name__)


class Spectrum(object):
    """
    This class is responsible for most of multinmrfit heavy work:

        * models initialization
        * spectrum simulation
        * spectrum fitting
        * sensitivity analysis
        * plotting

    :param data: DataFrame containing data (columns 'ppm' and 'intensity')
    :type data: class: pandas.DataFrame
    :param signals: signals to fit
    :type signals: dict
    :param models: available models
    :type models: dict
    :param offset: offset
    :type offset: dict
    
    """

    def __init__(self, data_path, dataset, expno, procno, rowno=None, window=None, data=None):

        logger.debug("create Spectrum object")

        # initialize data
        self.data_path = data_path
        self.dataset = dataset
        self.expno = expno
        self.procno = procno
        self.rowno = rowno
        self.window = window

        # set offset, fit_results, models and params attributes to default values
        self._initialize_attributes()

        # load NMR data
        if data is None:
            self.ppm, self.intensity = io.IoHandler.read_data(data_path, dataset, expno, procno, rowno=rowno, window=window)
        else:
            self.ppm, self.intensity = data.ppm.values.tolist(), data.intensity.values.tolist()

    
    def _initialize_attributes(self):
        
        self.offset = False
        self.fit_results = None
        self.models = {}
        self.params = pd.DataFrame(columns = ['signal_id', 'model', 'par', 'ini', 'lb', 'ub'])


    def _initialize_models(self, signals, available_models):

        # set (or reset if previously set) model-related attributes (parameters, models, etc)
        self._initialize_attributes()

        # for each signal
        for id, signal in signals.items():

            logger.debug("build Model for signal '{}'".format(id))

            # create a corresponding Model object
            self.models[id] = available_models[signal['model']]()

            # get default parameters & bounds
            _params = self.models[id].get_params()

            # add signal id
            _params.insert(0, 'signal_id', [id]*len(_params.index))

            # add global parameters indices to model object
            self.models[id]._par_idx = [i for i in range(len(self.params), len(_params.index)+len(self.params))]
            self.params = pd.concat([self.params, _params])

        # reset index
        self.params.reset_index(inplace=True, drop=True)

        logger.debug("parameters\n{}".format(self.params))


    def peak_picking(self, threshold):

        logger.debug("peak peaking")

        # perform peak picking
        peak_table = ng.peakpick.pick(self.intensity, pthres=threshold, algorithm='downward')
        peak_table = pd.DataFrame(peak_table)

        # add chemical shifts in ppm
        peak_table.insert(0, 'ppm', [self.ppm[int(i)] for i in peak_table['X_AXIS'].values])

        # add intensities
        peak_table.insert(0, 'intensity', [self.intensity[int(i)] for i in peak_table['X_AXIS'].values])

        logger.debug("peak table\n{}".format(peak_table))

        return peak_table


    def build_model(self, signals, available_models, offset=None):

        # initialize models
        self._initialize_models(signals, available_models)

        # update parameters
        self.set_params(signals)

        # set offset
        self.set_offset(offset)


    def _reset_fit_results(self):

        # silently remove estimated parameters & integrals from params
        self.params.drop(["opt", "opt_sd", "integral"], axis=1, inplace=True, errors="ignore")

        # reset fit_results
        self.fit_results = None

    def _set_param(self, id, par, k, v):
        """
        Update parameter both in spectrum object and in the corresponding model objects.
        Ensure internal consistency when setting a parameter.
        """

        # update parameter in model
        self.models[id].set_params(par, (k, v))
        # update self.params
        self.params.loc[(self.params["signal_id"] == id) & (self.params["par"] == par), k] = v  


    def set_params(self, signals):

        # raise an error if params not initialized (i.e. model has not been built)
        if not len(self.models):
            raise ValueError("Model of the spectrum has not been built, must call build_model() first.")

        # reset results of previous fit
        self._reset_fit_results()

        # update parameters values & bounds
        for id, signal in signals.items():
            for par, val in signal.get("par", {}).items():
                for k, v in val.items():
                    self._set_param(id, par, k, v)


    def set_offset(self, offset):

        # raise an error if params not initialized (i.e. model has not been built)
        if not len(self.models):
            raise ValueError("Model of the spectrum has not been built, must call build_model() first.")

        # reset results of previous fit
        self._reset_fit_results()

        # update offset to its new value
        if offset is None:
            if self.offset:
                self.params.drop(self.params[(self.params["signal_id"] == 'full_spectrum') & (self.params["par"] == 'offset')].index, inplace=True)
                self.offset = False
        else:
            if isinstance(offset, dict):
                if self.offset:
                    for k, v in offset.items():
                        self.params.loc[(self.params["signal_id"] == 'full_spectrum') & (self.params["par"] == 'offset'), k] = v
                else:
                    self.offset = True
                    default_offset_bound = 0.2 * np.max(self.intensity)
                    self.params.loc[len(self.params.index)] = ['full_spectrum', None, 'offset', offset.get('ini', 0), offset.get('lb', -default_offset_bound), offset.get('ub', default_offset_bound)]
            else:
                raise TypeError("offset must be a dict or None")
        

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
        between experimental and simulated data.
        :return: residuum (float)
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
        """
        Integrate all signals of spectrum.
        :return: area (dict)
        """

        if params is None:
            params = self.params['ini'].values.tolist()

        # simulate spectrum
        from_to = np.arange(bounds[0], bounds[1], (bounds[1] - bounds[0])/4000000.0)
        area = {}
        for name, model in self.models.items():
            area[name] = model.integrate([params[i] for i in model._par_idx], from_to)

        return area


    def _check_parameters(self):
        """
        Check initial parameters values are valid (i.e. floats between lower and upper bounds).
        :return: None
        """

        test_bounds = (self.params['ini'] < self.params['lb']) | (self.params['ini'] > self.params['ub'])
        if any(test_bounds):
            par_error = self.params.loc[test_bounds, 'par'].values.tolist()
            raise ValueError("initial values of parameters '{}' must be within bounds.".format(par_error))


    @staticmethod
    def linear_stats(res, ftol=2.220446049250313e-09):

        npar = len(res.x)
        tmp_i = np.zeros(npar)
        standard_deviations = np.array([np.inf]*npar)

        for i in range(npar):
            tmp_i[i] = 1.0
            hess_inv_i = res.hess_inv(tmp_i)[i]
            sd_i = np.sqrt(max(1.0, res.fun) * ftol * hess_inv_i)
            tmp_i[i] = 0.0
            #logger.debug('sd p{0} = {1:12.4e} ± {2:.1e}'.format(i, res.x[i], sd_i))
            #logger.debug(f"   (rsd = {sd_i/res.x[i]}")
            standard_deviations[i] = sd_i

        return standard_deviations


    def fit(self, method="L-BFGS-B"):
        """
        Fit spectrum.
        """

        logger.debug("fit spectrum")

        # check parameters
        self._check_parameters()
        
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
        
        # calculate standard deviation on estimated parameters (linear statistics)
        standard_deviations = self.linear_stats(self.fit_results)

        # add estimated parameters & sds
        self.params['opt'] = self.fit_results.x
        self.params['opt_sd'] = standard_deviations

        # scale back estimated parameters
        self.params.loc[self.params['par'].isin(["intensity", "offset"]), ["opt", "opt_sd"]] *= scaling_factor

        # simulate spectrum from estimated parameters
        self.fit_results.best_fit = self.simulate(self.params['opt'].values.tolist())

        # integrate spectrum
        integrals = self.integrate(self.params['opt'].values.tolist())
        self.params['integral'] = [integrals[i] if i != 'full_spectrum' else np.nan for i in self.params['signal_id'].values]

        logger.debug("parameters\n{}".format(self.params))


    def plot(self, exp=True, ini=False, fit=False, pp=None):
        """Plot experimental and simulated (from initial values and best fit) spectra."""
        
        logger.debug("create plot")
        
        display_fit = fit and ('opt' in self.params.columns)
        
        if display_fit:
            fig_full = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3])
        else:
            fig_full = make_subplots(rows=1, cols=1)
        
        # generate individual plots

        if exp:
            fig_exp = go.Scatter(x=self.ppm, y=self.intensity, mode='markers', name='exp. spectrum', marker_color="#386CB0")
            fig_full.add_trace(fig_exp, row=1, col=1)

        if ini:
            if len(self.params.index):
                ini_intensity = self.simulate(params = self.params['ini'].values.tolist())
                fig_ini = go.Scatter(x=self.ppm, y=ini_intensity, mode='lines', name='initial values', marker_color="#7FC97F")
                fig_full.add_trace(fig_ini, row=1, col=1)
            else:
                raise ValueError("Model of the spectrum has not been built, must call build_model() first.")

        if display_fit:
            if self.fit_results is None:
                raise ValueError("Spectrum has not been fitted, must call fit() first.")
            else:
                fig_fit = go.Scatter(x=self.ppm, y=self.fit_results.best_fit, mode='lines', name='best fit', marker_color="#EF553B")
                fig_full.add_trace(fig_fit, row=1, col=1)

                residuum = self.fit_results.best_fit - self.intensity
                fig_resid = go.Scatter(x=self.ppm, y=residuum, mode='lines', name='residuum', marker_color="#AB63FA")
                fig_full.add_trace(fig_resid, row=2, col=1)

        if isinstance(pp, pd.DataFrame):
            x = pp['ppm'].values.tolist()
            offset_plot = 0.05 * np.max(self.intensity)
            y = [i + offset_plot for i in pp['intensity'].values]
            fig_pp = go.Scatter(x=x, y=y, mode='markers', name='peaks', marker_symbol="arrow-down", marker_line_width=1.2, marker_size=9, marker_color="#FDC086")
            fig_full.add_trace(fig_pp, row=1, col=1)


        fig_full['layout']['xaxis']['title']='chemical shift (ppm)'
        fig_full['layout']['yaxis']['title']='intensity'
        if display_fit:
            fig_full['layout']['xaxis2']['title']='chemical shift (ppm)'
            fig_full['layout']['yaxis2']['title']='intensity'
        fig_full.update_yaxes(exponentformat="power", showexponent="last")
        fig_full.update_xaxes(autorange="reversed")

        return fig_full