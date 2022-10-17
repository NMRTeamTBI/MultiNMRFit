import warnings
import logging
import threading

warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from scipy.optimize import minimize, differential_evolution

import multinmrfit.multiplets as nfm
import multinmrfit.ui_new as nfui

logger = logging.getLogger(__name__)

def update_resolution(constraints, x_fit_):
    delta = abs(x_fit_[1]-x_fit_[0])
    constraints[3] = (delta, constraints[3][1])
    return constraints

def update_position(constraints, x_fit_):
    constraints[0] = (np.min(x_fit_), np.max(x_fit_))
    return constraints

def get_fitting_parameters(
    peakpicking_data,
    x_fit_,
    scaling_factor,
    offset=False
    ):
    ini_params, ini_constraints, name_parameters = [], [], []
    cluster_list =  peakpicking_data.Cluster.unique()
    d_id = {k:[] for k in cluster_list}
    d_mapping, d_clustering = nfm.mapping_multiplets()
    Initial_offset = 0
    for n in cluster_list:
        _cluster_ = peakpicking_data.loc[peakpicking_data.Cluster==n]
        id_cluster = str(len(_cluster_)) + "".join(i for i in set(_cluster_.Options.values.tolist()))
        _multiplet_type_ = d_clustering[id_cluster]
        _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
        Init_Val = nfm.Peak_Initialisation(_multiplet_type_,Peak_Picking_Results=_cluster_,scaling_factor=scaling_factor)
        d_id[n] = (_multiplet_type_function, [len(ini_params), len(ini_params)+len(Init_Val)], _multiplet_type_)
        ini_params.extend(Init_Val)
        upd_cons = update_resolution(d_mapping[_multiplet_type_]['constraints'], x_fit_)
        upd_cons = update_position(upd_cons, x_fit_)
        ini_constraints.extend(upd_cons)
        name_parameters.extend(d_mapping[_multiplet_type_]['params'])
    if offset:
        ini_params.extend([Initial_offset])
        ini_constraints.extend([(-0.1, 0.1)])
    return d_id, ini_params, ini_constraints, name_parameters

def simulate_data(x_fit_, fit_par, d_id, scaling_factor, offset=False):
    # initialize simulated spectrum at 0
    sim_intensity = np.zeros(len(x_fit_))
    # add subspectrum of each spin system
    for n in d_id.keys():
        # get parameters of spin system
        params = fit_par[d_id[n][1][0]:d_id[n][1][1]]
        # simulate and add corresponding subspectrum
        sim_intensity += d_id[n][0](x_fit_, *params)
    # add offset (corresponds to 0-order baseline correction)
    if offset:
        sim_intensity += fit_par[-1]
    # multiply by scaling factor (required for stable minimization)
    sim_intensity *= scaling_factor
    return sim_intensity

def fit_objective(
    fit_par,
    x_fit_,
    y_fit_,
    d_id,
    scaling_factor,
    offset=False
    ):
    sim_intensity = simulate_data(x_fit_,fit_par, d_id, scaling_factor, offset=offset)
    rmsd = np.sqrt(np.mean((sim_intensity - y_fit_)**2))
    return rmsd

def refine_constraints(initial_fit_values, bounds_fit, name_parameters, relative_window=None):
    logger.debug(f"old bounds: {bounds_fit}")
    # update parameters based on dict(k, v) where k is a string used to identify the parameter, and v is the allowed (relative) parameter window
    if relative_window is None:
        relative_window = {"x0":0.001, "J":0.05, "lw":0.3}
    for k, v in relative_window.items():
        idx = [i for i,j in enumerate(name_parameters) if k in j]
        for i in idx:
            ini_val = initial_fit_values[i]
            upd_lb = ini_val*(1-v)
            upd_up =  ini_val*(1+v)
            if k == 'a' and upd_lb < 0.:
                upd_lb = 0.
            if k == 'a' and upd_up > 1.:
                upd_up = 1.
            bounds_fit[i] = (upd_lb, upd_up)
    logger.debug(f"new bounds: {bounds_fit}")
    return bounds_fit

def compute_statistics(res, ftol=2.220446049250313e-09):
    npar = len(res.x)
    tmp_i = np.zeros(npar)
    standard_deviations = np.array([np.inf]*npar)
    for i in range(npar):
        tmp_i[i] = 1.0
        hess_inv_i = res.hess_inv(tmp_i)[i]
        sd_i = np.sqrt(max(1.0, res.fun) * ftol * hess_inv_i)
        tmp_i[i] = 0.0
        logger.debug('sd p{0} = {1:12.4e} ± {2:.1e}'.format(i, res.x[i], sd_i))
        logger.debug(f"   (rsd = {sd_i/res.x[i]}")
        standard_deviations[i] = sd_i
    return standard_deviations

def run_single_fit_function(up, 
                            fit, 
                            intensities, 
                            fit_results, 
                            stat_results, 
                            x_spectrum_fit, 
                            peak_picking_data, 
                            scaling_factor,
                            use_previous_fit,
                            writing_to_file=True,
                            offset=False,
                            option_optimizer='L-BFGS-B',
                            relative_window=None
                            ):

    d_id, initial_fit_values, bounds_fit, name_parameters = get_fitting_parameters(peak_picking_data, x_spectrum_fit, scaling_factor, offset=offset)
    if use_previous_fit :
        initial_fit_values = list(fit_results.iloc[fit[1]-1 if up else fit[1]+1].values)
        bounds_fit = refine_constraints(initial_fit_values, bounds_fit, name_parameters, relative_window=relative_window)
    try:
        intensities = intensities[fit[0],:]
        if option_optimizer=='L-BFGS-B':
            res_fit = minimize(
                fit_objective,
                x0=initial_fit_values,                
                bounds=bounds_fit,
                method='L-BFGS-B',
                options={'maxcor': 30},
                args=(x_spectrum_fit, intensities, d_id, scaling_factor, offset)
                )            
        elif option_optimizer=='DE + L-BFGS-B':
            res_fit_de = differential_evolution(
                fit_objective,
                x0=initial_fit_values,                
                bounds=bounds_fit,
                args=(x_spectrum_fit, intensities, d_id, scaling_factor, offset)
                )
            res_fit = minimize(
                fit_objective,
                x0=res_fit_de.x,                
                bounds=bounds_fit,
                method='L-BFGS-B',
                options={'maxcor': 30},
                args=(x_spectrum_fit, intensities, d_id, scaling_factor, offset)
                )
        else:
            logger.error('Wrong optimizer selected: '+option_optimizer)
        logger.debug(res_fit)
        res_stats = compute_statistics(res_fit)
        logger.debug(res_stats)
        res_fit.res_stats = res_stats.tolist()
        
        if not writing_to_file:
            return res_fit
        else:
            fit_results.loc[fit[1],:] = res_fit.x.tolist()
            stat_results.loc[fit[1],:] = res_stats.tolist()

    except:
        logger.error('An unknown error has occured when fitting spectra: '+str(fit[1]))

