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
    """This class is responsible for most of multinmrfit heavy work:

        * data loading
        * peak picking
        * model initialization
        * spectrum simulation
        * spectrum fitting
        * sensitivity analysis
        * plotting
    """

    def __init__(self, data, window: tuple = None, from_ref: int = None, rowno: int = None) -> None:
        """Construct the Spectrum object.

        Args:
            data (dataframe | dict): input data, either a dataframe containing the chemical shifts (with columns 'ppm' and 
                                     'intensity'), or a dict to load the data from Topspin files.
            window (tuple, optional): lower and upper bounds of the window of interest (in ppm) or full spectrum if None. Defaults to None.
        """

        logger.debug("create Spectrum object")

        # load NMR data
        loader = io.IoHandler()
        dataset = loader.load_data(data, window=window, rowno=rowno)

        # set spectrum-related attributes
        self.data_path = dataset["data_path"]
        self.dataset = dataset["dataset"]
        self.expno = dataset["expno"]
        self.procno = dataset["procno"]
        self.rowno = dataset["rowno"]
        self.window = dataset["window"]
        self.ppm = dataset["ppm"]
        self.ppm_limits = (min(self.ppm), max(self.ppm))
        self.region = str(round(self.ppm_limits[0], 2)) + " | " + str(round(self.ppm_limits[1], 2))
        self.intensity = dataset["intensity"]
        self.peakpicking_threshold = None
        self.from_ref = from_ref
        self.edited_peak_table = None
        self._edited_peak_table = None
        self.user_models = None
        self.signals = None

        # initialize model-related attributes (models, params, offset and fit_results) at default values
        self._set_default_model_attributes()

    
    def _set_default_model_attributes(self):
        """Initialize model-related attributes at default values.
        """   

        self.models = {}
        self.params = pd.DataFrame(columns = ['signal_id', 'model', 'par', 'ini', 'lb', 'ub'])
        self.offset = False
        self.fit_results = None


    def _initialize_models(self, signals: dict, available_models: dict) -> None:
        """Initialize models of each signal.

        Args:
            signals (dict): signals
            available_models (dict): models
        """

        # set (or reset if previously set) model-related attributes (parameters, models, etc)
        self._set_default_model_attributes()

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

            # add model parameters to global parameters
            self.params = _params if self.params.empty else pd.concat([self.params, _params])

        # reset index
        self.params.reset_index(inplace=True, drop=True)

        logger.debug("parameters\n{}".format(self.params))


    def _reset_fit_results(self) -> None:
        """Remove results of the last fit.
        """

        # silently remove estimated parameters & integrals from params
        self.params.drop(["opt", "opt_sd", "integral"], axis=1, inplace=True, errors="ignore")

        # reset fit_results
        self.fit_results = None


    def _set_param(self, id: str, par: str, k: str, v: float) -> None:
        """Update parameter both in spectrum object and in the corresponding model objects.
        Ensure internal consistency when setting a parameter.

        Args:
            id (str): signal id
            par (str): parameter name
            k (str): parameter key ('ini', 'lb', 'ub')
            v (float): value
        """

        # update parameter in model
        self.models[id].set_params(par, (k, v))

        # update self.params
        self.params.loc[(self.params["signal_id"] == id) & (self.params["par"] == par), k] = v  


    @staticmethod
    def _simulate(params: list, ppm: list, models: dict, offset: bool = False) -> list:
        """Simulate spectrum

        Args:
            params (list): parameters values
            ppm (list): chemical shifts
            models (dict): models of all signals
            offset (bool, optional): offset (provided as last element of params) added to spectrum if True. Defaults to False.

        Returns:
            list: simulated intensities
        """

        # initialize spectrum at offset or 0
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
    def _calculate_cost(params: list, func: callable, models: dict, ppm: list, intensity: list, offset: bool = False) -> float:
        """Calculate residuum as sum of squared differences between experimental and simulated data.

        Args:
            params (list): parameters values
            func (function): simulation function
            models (dict): models of all signals
            ppm (list): chemical shifts
            intensity (list): measured intensities
            offset (bool, optional): offset (provided as last element of params) added to spectrum if True. Defaults to False.

        Returns:
            float: residuum
        """

        # simulate spectrum
        simulated_spectrum = func(params, ppm, models, offset=offset)

        # calculate sum of squared residuals
        residuum = np.sum(np.square(simulated_spectrum - intensity))

        return residuum


    def _check_parameters(self) -> None:
        """
        Check initial parameters values are valid (i.e. numbers between lower and upper bounds).
        """

        # check initial values & bounds are numeric
        for i in ['ini', 'lb', 'ub']:
            if not np.issubdtype(self.params[i].dtype, np.number):
                raise ValueError("Values '{}' must be numeric for all parameters.".format(i))

        # check initial values are within bounds
        test_bounds = (self.params['ini'] < self.params['lb']) | (self.params['ini'] > self.params['ub'])
        if any(test_bounds):
            par_error = self.params.loc[test_bounds, 'par'].values.tolist()
            raise ValueError("Initial values of parameters '{}' must be within bounds.".format(par_error))


    @staticmethod
    def _linear_stats(res, ftol: float = 2.220446049250313e-09) -> list:
        """Calculate standard deviation on estimated parameters using linear statistics.

        Args:
            res (scipy.optimize.OptimizeResult): fit results
            ftol (float, optional): ftol of optimization. Defaults to 2.220446049250313e-09.

        Returns:
            list: standard deviations
        """

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


    def _check_model(self) -> None:

        # raise an error if params not initialized (i.e. model has not been built)
        if not len(self.models):
            raise ValueError("Model of the spectrum has not been built, must call build_model() first.")


    def _check_fit_results(self) -> None:

        # raise an error if experimental spectrum has not been fitted
        if self.fit_results is None:
            raise ValueError("Spectrum has not been fitted, must call fit() first.")


    def peak_picking(self, threshold: int) -> pd.DataFrame:
        """Peak picking.

        Args:
            threshold (int): threshould value for peak picking.

        Returns:
            pd.DataFrame: peak table
        """

        logger.debug("peak peaking")

        # perform peak picking
        try:
            peak_table = ng.peakpick.pick(self.intensity, pthres=threshold, algorithm='downward')
            peak_table = pd.DataFrame(peak_table)
            
        except:
            logger.debug("No peak found.")
            peak_table = pd.DataFrame(columns = ['X_AXIS', 'cID', 'X_LW', 'VOL'])

        self.peakpicking_threshold = threshold

        # add chemical shifts in ppm
        peak_table.insert(0, 'ppm', [self.ppm[int(i)] for i in peak_table['X_AXIS'].values])

        # add intensities
        peak_table.insert(0, 'intensity', [self.intensity[int(i)] for i in peak_table['X_AXIS'].values])

        # drop peak position in points, volumes and linewidths in points
        peak_table.drop(['X_AXIS','VOL','cID'],axis=1,inplace=True)
        # all clear cluster_ids from nmrglue to be replace from cluster_ids from mulitnmrfit
        peak_table['cID'] = ""

        # change type of the cluster column only to allow cluster names
        peak_table["cID"] = peak_table['cID'].astype(str) 

        # sort by peak position in ppm 
        peak_table.sort_values(by=['ppm'],inplace=True)

        # Change Column names
        peak_table.reset_index(inplace=True,drop=True)

        # Change columns order
        peak_table = peak_table[['ppm','intensity','X_LW','cID']]

        peak_table.drop('X_LW', axis=1, inplace=True)

        logger.debug("peak table\n{}".format(peak_table))

        return peak_table


    def build_model(self, signals: dict, available_models: dict, offset: dict = None) -> None:
        """Build models of each signal to simulate the full spectrum.

        Args:
            signals (dict): signals
            available_models (dict): models
            offset (dict, optional): offset. Defaults to None.
        """

        # initialize models
        self._initialize_models(signals, available_models)

        # set signals
        self.signals = signals

        # update parameters
        self.update_params(signals)

        # set offset
        self.update_offset(offset)


    def update_params(self, signals: dict) -> None:
        """Update parameters (initial values, lower and upper bounds).

        Args:
            signals (dict): signals
        """

        # check the model has been built
        self._check_model()

        # reset results of previous fit
        self._reset_fit_results()

        # update parameters values & bounds
        for id, signal in signals.items():
            for par, val in signal.get("par", {}).items():
                for k, v in val.items():
                    self._set_param(id, par, k, v)
                    #self.signals[id]["par"][k] = v


    def update_offset(self, offset: dict) -> None:
        """Update offset (initial value, lower and upper bounds).

        Args:
            offset (dict): offset
        """

        # check the model has been built
        self._check_model()

        # reset results of previous fit
        self._reset_fit_results()

        # update offset to its new value
        if offset is None:
            if self.offset:
                self.params.drop(self.params[
                                     (self.params["signal_id"] == 'full_spectrum') & (self.params["par"] == 'offset')
                                 ].index, inplace=True)
                self.offset = False
        else:
            if isinstance(offset, dict):
                if self.offset:
                    for k, v in offset.items():
                        self.params.loc[
                            (self.params["signal_id"] == 'full_spectrum') & (self.params["par"] == 'offset'), k] = v
                else:
                    self.offset = True
                    default_offset_bound = 0.2 * np.max(self.intensity)
                    self.params.loc[len(self.params.index)] = [
                        'full_spectrum',
                        None,
                        'offset',
                        offset.get('ini', 0),
                        offset.get('lb', -default_offset_bound),
                        offset.get('ub', default_offset_bound)
                    ]
            else:
                raise TypeError("offset must be a dict or None")
        

    def simulate(self, params: list = None) -> list:
        """Simulate spectrum.

        Args:
            params (list, optional): parameters values. Defaults to None.

        Returns:
            list: simulated intensities
        """
        
        # check the model has been built
        self._check_model()

        if params is None:
            params = self.params['ini'].values.tolist()

        # simulate spectrum
        simulated_spectra = self._simulate(params, self.ppm, self.models, offset=self.offset)

        return simulated_spectra


    def integrate(self, params: list = None, bounds: list = [-100.0, 300.0]) -> dict:
        """Integrate each signal of the spectrum.

        Args:
            params (list, optional): parameters values, initial values if None. Defaults to None.
            bounds (list, optional): bounds for integration. Defaults to [-100.0, 300.0].

        Returns:
            dict: area of each signal.
        """

        # check the model has been built
        self._check_model()

        if params is None:
            params = self.params['ini'].values.tolist()

        # simulate spectrum
        from_to = np.arange(bounds[0], bounds[1], (bounds[1] - bounds[0])/4000000.0)
        area = {}
        for name, model in self.models.items():
            area[name] = model.integrate([params[i] for i in model._par_idx], from_to)

        return area


    def fit(self, method: str = "L-BFGS-B"):
        """Fit spectrum.

        Args:
            method (str, optional): optimization method, "L-BFGS-B" or "differential_evolution". Defaults to "L-BFGS-B".

        Returns:
            scipy.optimize.OptimizeResult: optimization results.
        """

        logger.debug("fit spectrum")

        # check the model has been built
        self._check_model()

        # check parameters
        self._check_parameters()
        
        # set scaling factor to stabilize convergence
        mean_sp = np.mean(self.intensity)
        scaling_factor = 1 if -1 < mean_sp < 1 else abs(mean_sp)

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
                options={'maxcor': 30, 'maxls': 30}
            )

        else:

            raise ValueError("optimization method '{}' not implemented".format(method))
        
        # calculate standard deviation on estimated parameters (linear statistics)
        standard_deviations = self._linear_stats(self.fit_results)

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


    def plot(self, exp: bool = True, ini: bool = False, fit: bool = False, colored_area: bool = False, pp: pd.DataFrame = None, threshold: float = None) -> go.Figure:
        """Plot experimental and simulated (from initial values and best fit) spectra and peak picking results.

        Args:
            exp (bool, optional): plot experimental spectrum if True. Defaults to True.
            ini (bool, optional): plot spectrum simulated from initial parameters values if True. Defaults to False.
            fit (bool, optional): plot spectrum simulated from the best fit if True. Defaults to False.
            pp (pd.DataFrame, optional): plot peak picking results. Defaults to None.

        Returns:
            go.Figure: plotly figure
        """
        
        logger.debug("create plot")
        
        if fit:
            self._check_fit_results()
            fig_full = make_subplots(rows=2, cols=1, row_heights=[0.7, 0.3], shared_xaxes=True)
        else:
            fig_full = make_subplots(rows=1, cols=1)
        
        # generate individual plots

        if exp:
            mode = 'markers' if fit else 'lines'
            fig_exp = go.Scatter(x=self.ppm, y=self.intensity, mode=mode, name='exp. spectrum', marker_color="#386CB0")
            fig_full.add_trace(fig_exp, row=1, col=1)

        if ini:
            self._check_model()
            ini_intensity = self.simulate(params = self.params['ini'].values.tolist())
            fig_ini = go.Scatter(x=self.ppm, y=ini_intensity, mode='lines', name='initial values', marker_color="#7FC97F")
            fig_full.add_trace(fig_ini, row=1, col=1)

        if colored_area:
            for name, model in self.models.items():
                model_intensity = model.simulate([self.params['opt'].values.tolist()[i] for i in model._par_idx], np.array(self.ppm.values.tolist()))
                fig_colored_area = go.Scatter(
                    x=self.ppm, 
                    y=model_intensity,
                    fill="tozeroy",
                    mode='lines', 
                    name='signal ' + str(name))
                fig_full.add_trace(fig_colored_area, row=1, col=1)

        if fit:
            fig_fit = go.Scatter(x=self.ppm, y=self.fit_results.best_fit, mode='lines', name='best fit', marker_color="#EF553B")
            fig_full.add_trace(fig_fit, row=1, col=1)
            
            residuum = self.fit_results.best_fit - self.intensity
            fig_resid = go.Scatter(x=self.ppm, y=residuum, mode='lines', name='residuum', marker_color="#AB63FA")
            fig_full.add_trace(fig_resid, row=2, col=1)
            
        if isinstance(pp, pd.DataFrame):
            x = pp['ppm'].values
            offset_plot = 0.05 * np.max(self.intensity)
            y = [i + offset_plot for i in pp['intensity'].values]
            fig_pp = go.Scatter(x=x, y=y, mode='markers', name='peaks detected', marker_symbol="arrow-down", marker_line_width=1.2, marker_size=9, marker_color="#FDC086")
            fig_full.add_trace(fig_pp, row=1, col=1)

        if isinstance(threshold, float):
            fig_full.add_hline(y=threshold,line_width=3, line_dash="dash", line_color="cadetblue", name='threshold')

        fig_full.update_layout(plot_bgcolor="white", xaxis=dict(linecolor="black", mirror=True, showline=True), yaxis=dict(linecolor="black", mirror=True, showline=True, title='intensity'),legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        if fit:
            fig_full.update_layout(plot_bgcolor="white", xaxis2=dict(linecolor="black", mirror=True, showline=True, title='chemical shift (ppm)'), yaxis2=dict(linecolor="black", mirror=True, showline=True, title='residuum'))
            # add horizontal line at y=0 on residuum
            fig_full.update_layout(shapes=[{'type': 'line','y0':0,'y1': 0,'x0':np.min(self.ppm), 'x1':np.max(self.ppm),'xref':'x2','yref':'y2', 'line': {'color': 'black','width': 1.0, 'dash': 'dash'}}])
        else:
            fig_full.update_layout(xaxis=dict(title='chemical shift (ppm)'))

        fig_full.update_yaxes(exponentformat="power", showexponent="last")
        fig_full.update_xaxes(autorange="reversed", ticks="outside")
        fig_full.update_layout(plot_bgcolor="white", xaxis=dict(linecolor="black"), yaxis=dict(linecolor="black"))
        fig_full.update_xaxes(autorange=False, range=[np.max(self.ppm), np.min(self.ppm)])

        return fig_full

