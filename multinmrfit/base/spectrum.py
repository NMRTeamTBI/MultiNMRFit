"""
PhysioFit software main module
"""

import logging

import numpy as np
import pandas as pd
from scipy.optimize import minimize, differential_evolution
from scipy.stats import chi2

from multinmrfit.logger import initialize_fitter_logger
from multinmrfit.models.base_model import Model

mod_logger = logging.getLogger("multinmrfit.base.spectrum")


class Spectrum:
    """
    This class is responsible for most of Physiofit's heavy lifting. Features included are:

        * loading of data from **csv** or **tsv** file
        * **equation system initialization** using the following analytical functions (in absence of lag and
          degradation:

            X(t) = X0 * exp(mu * t)
            Mi(t) = qMi * (X0 / mu) * (exp(mu * t) - 1) + Mi0

        * **simulation of data points** from given initial parameters
        * **cost calculation** using the equation:

            residuum = sum((sim - meas) / sd)²

        * **optimization of the initial parameters** using `scipy.optimize.minimize ('Differential evolution', with polish with 'L-BFGS-B' method) <https://docs.scipy.org/doc/scipy/reference/optimize.minimize-lbfgsb.html#optimize-minimize-lbfgsb>`_
        * **sensitivity analysis, khi2 tests and plotting**

    :param data: DataFrame containing data and passed by IOstream object
    :type data: class: pandas.DataFrame
    :param model: Model to initialize parameters and optimize
    :type model: physiofit.models.base_model.Model
    :param mc: Should Monte-Carlo sensitivity analysis be performed (default=True)
    :type mc: Boolean
    :param iterations: number of iterations for Monte-Carlo simulation (default=50)
    :type iterations: int
    :param sd: sd matrix used for residuum calculations. Can be:

                * a matrix with the same dimensions as the measurements matrix (but without the time column)
                * a named vector containing sds for all the metabolites provided in the input file
                * 0  in which case the matrix is automatically constructed from default values
                * a dictionary with the data column headers as keys and the associated value as a scalar or list

    :type sd: int, float, list, dict or ndarray
    """

    def __init__(
            self,
            data,
            cluster={},
            all_models={},
            mc=True,
            iterations=100,
            debug_mode=False
    ):


        self.intensity = data.intensity
        self.ppm = data.ppm
        self.cluster = cluster
        #self.mc = mc
        #self.iterations = iterations
        #self.debug_mode = debug_mode
        #if not hasattr(self, "logger"):
        #    self.logger = initialize_fitter_logger(self.debug_mode)
        
        self.models = None
        #self.simulated_data = None
        #self.optimize_results = None
        #self.parameter_stats = None
        #self.opt_params_sds = None
        #self.matrices_ci = None
        #self.opt_conf_ints = None
        #self.khi2_res = None

        self.initialize_models(all_models)

    def initialize_models(self, all_models):
        self.models = {}
        self.params = pd.DataFrame(columns = ['signal_id', 'model', 'par', 'ini', 'lb', 'ub'])

        for id, peak in self.cluster.items():
            self.models[id] = {}
            self.models[id]["model"] = all_models[peak['model']]
            print(self.models[id]["model"])

            _params = self.models[id]["model"].get_params()
            
            self.models[id]["par_idx"] = [i for i in range(len(self.params), len(_params)+len(self.params))]
            _params.insert(0, 'signal_id', [id]*len(_params))
            print(_params)
            self.params = pd.concat([self.params, _params])


    def simulate(params, ppm, models):
        simulated_spectra = np.zeros(len(ppm))
        for model in models.values():
            # get parameters
            idx = model["par_idx"]
            # run simulation
            simulated_signal = model["model"].simulate(params[idx], ppm)
            simulated_spectra += simulated_signal
        return simulated_spectra



    def _calculate_cost(params, func, models, ppm, intensity):
        """
        Calculate the cost (residue) using the square of
        simulated-experimental over the SDs
        """

        simulated_spectrum = func(params, ppm, models)
        residuum = np.square(simulated_spectrum - intensity)

        return residuum


    @staticmethod
    def fit(self, method: str):
        """
        Run the optimization on input parameters using the cost function and
        Scipy minimize (L-BFGS-B method that is deterministic and uses the
        gradient method for optimizing)
        """

        #if method == "differential_evolution":
        #    optimize_results = differential_evolution(
        #        Spectrum._calculate_cost, bounds=bounds,
        #        args=(
        #        func, exp_data_matrix, time_vector, non_opt_params, sd_matrix),
        #        polish=True, x0=params
        #    )
        #elif method == "L-BFGS-B":
        #    optimize_results = minimize(
        #        Spectrum._calculate_cost, x0=params,
        #        args=(
        #        func, exp_data_matrix, time_vector, non_opt_params, sd_matrix),
        #        method="L-BFGS-B", bounds=bounds, options={'maxcor': 30}
        #    )
        #else:
        #    raise ValueError(f"{method} is not implemented")

        x0 = self.params['ini'].values.tolist()
        bounds = list(zip(self.params['lb'], self.params['ub']))
        
        optimize_results = minimize(self._calculate_cost,
                                    x0=x0,
                                    args=(self.simulate, self.models, self.ppm, self.intensity),
                                    method="L-BFGS-B", bounds=bounds, options={'maxcor': 30})

        return optimize_results

    def monte_carlo_analysis(self):
        """
        Run a monte carlo analysis to calculate optimization standard
        deviations on parameters and simulated data points
        """

        if not self.optimize_results:
            raise RuntimeError(
                "Running Monte Carlo simulation without having run the "
                "optimization is impossible as best fit results are needed to "
                "generate the initial simulated matrix"
            )

        self.logger.info(
            f"Running monte carlo analysis. Number of iterations: "
            f"{self.iterations}\n"
        )

        # Store the optimized results in variable that will be overridden on
        # every pass
        opt_res = self.optimize_results
        opt_params_list = []
        matrices = []

        for _ in range(self.iterations):
            new_matrix = self._apply_noise()

            # We optimise the parameters using the noisy matrix as input
            opt_res = Spectrum._run_optimization(
                opt_res.x, self.simulate, new_matrix, self.model.time_vector,
                self.model.fixed_parameters, self.sd, self.model.bounds(),
                "L-BFGS-B"
            )

            # Store the new simulated matrix in list for later use
            matrices.append(
                self.simulate(
                    opt_res.x, new_matrix, self.model.time_vector,
                    self.model.fixed_parameters
                )
            )

            # Store the new optimised parameters in list for later use
            opt_params_list.append(opt_res.x)

        # Build a 3D array from all the simulated matrices to get standard
        # deviation on each data point
        matrices = np.array(matrices)
        self.matrices_ci = {
            "lower_ci": np.percentile(matrices, 2.5, axis=0),
            "higher_ci": np.percentile(matrices, 97.5, axis=0)
        }

        # Compute the statistics on the list of parameters: means, sds,
        # medians and confidence interval
        self._compute_parameter_stats(opt_params_list)
        self.logger.info(f"Optimized parameters statistics:")
        for key, value in self.parameter_stats.items():
            self.logger.info(f"{key}: {value}")

        # Apply nan mask to be coherent with the experimental matrix
        nan_lower_ci = np.copy(self.matrices_ci['lower_ci'])
        nan_higher_ci = np.copy(self.matrices_ci['higher_ci'])
        nan_lower_ci[np.isnan(self.experimental_matrix)] = np.nan
        nan_higher_ci[np.isnan(self.experimental_matrix)] = np.nan

        self.logger.info(
            f"Simulated matrix lower confidence interval:\n{nan_lower_ci}\n"
        )
        self.logger.info(
            f"Simulated matrix higher confidence interval:\n{nan_higher_ci}\n"
        )
        return

    def _compute_parameter_stats(self, opt_params_list):
        """
        Compute statistics on the optimized parameters from the monte carlo
        analysis.

        :param opt_params_list: list of optimized parameter arrays generated
                                during the monte carlo analysis
        :return: parameter stats attribute containing means, sds, medians, low
                 and high CI
        """

        opt_params_means = np.mean(np.array(opt_params_list), 0)
        opt_params_sds = np.std(np.array(opt_params_list), 0)
        opt_params_meds = np.median(np.array(opt_params_list), 0)
        conf_ints = np.column_stack((
            np.percentile(opt_params_list, 2.5, 0),
            np.percentile(opt_params_list, 97.5, 0)
        ))

        self.parameter_stats.update({
            "mean": opt_params_means,
            "sd": opt_params_sds,
            "median": opt_params_meds,
            "CI_2.5": conf_ints[:, 0],
            "CI_97.5": conf_ints[:, 1]
        })

        # self.parameter_stats_df = DataFrame()

    def khi2_test(self):

        number_measurements = np.count_nonzero(
            ~np.isnan(self.experimental_matrix)
        )
        number_params = len(self.model.parameters_to_estimate)
        dof = number_measurements - number_params
        cost = self._calculate_cost(
            self.optimize_results.x, self.simulate, self.experimental_matrix,
            self.model.time_vector, self.model.fixed_parameters, self.sd
        )
        p_val = chi2.cdf(cost, dof)

        khi2_res = {
            "khi2_value": cost,
            "number_of_measurements": number_measurements,
            "number_of_params": number_params,
            "Degrees_of_freedom": dof,
            "p_val": p_val
        }
        self.khi2_res = DataFrame.from_dict(
            khi2_res, "index", columns=["Values"]
        )

        self.logger.info(f"khi2 test results:\n"
                         f"khi2 value: {cost}\n"
                         f"Number of measurements: {number_measurements}\n"
                         f"Number of parameters to fit: {number_params}\n"
                         f"Degrees of freedom: {dof}\n"
                         f"p-value = {p_val}\n")

        if p_val < 0.95:
            self.logger.info(
                f"At level of 95% confidence, the model fits the data good "
                f"enough with respect to the provided measurement SD. "
                f"Value: {p_val}"
            )

        else:
            self.logger.info(
                f"At level of 95% confidence, the model does not fit the data "
                f"good enough with respect to the provided measurement SD. "
                f"Value: {p_val}\n"
            )

    @staticmethod
    def _add_noise(vector, sd):
        """
        Add random noise to a given array using input standard deviations.

        :param vector: input array on which to apply noise
        :type vector: class: numpy.ndarray
        :param sd: standard deviation to apply to the input array
        :type sd: class: numpy.ndarray
        :return: noisy ndarray
        """

        output = np.random.default_rng().normal(
            loc=vector, scale=sd, size=vector.size
        )
        return output

    def _apply_noise(self):
        """
        Apply noise to the simulated matrix obtained using optimized
        parameters. SDs are obtained from the sd matrix
        """

        new_matrix = np.array([
            Spectrum._add_noise(self.simulated_matrix[idx, :], sd)
            for idx, sd in enumerate(self.sd)
        ])
        return new_matrix
