import warnings
import logging
import threading

warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from scipy.optimize import minimize

import multinmrfit.multiplets as nfm
import multinmrfit.ui as nfui

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

def refine_constraints(initial_fit_values, bounds_fit, name_parameters):
    logger.debug(f"old bounds: {bounds_fit}")
    # update parameters based on dict(k, v) where k is a string used to identify the parameter, and v is the allowed (relative) parameter window
    relative_window = {"J":0.05, "lw":0.3}
    for k, v in relative_window.items():
        idx = [i for i,j in enumerate(name_parameters) if k in j]
        for i in idx:
            ini_val = initial_fit_values[i]
            bounds_fit[i] = (ini_val*(1-v), ini_val*(1+v))
    logger.debug(f"new bounds: {bounds_fit}")
    return bounds_fit

def compute_statistics(res, ftol=2.220446049250313e-09):
    npar = len(res.x)
    tmp_i = np.zeros(npar)
    standard_deviations = np.array([np.inf]*npar)
    for i in range(npar):
        tmp_i[i] = 1.0
        hess_inv_i = res.hess_inv(tmp_i)[i]
        sd_i = np.sqrt(max(1, abs(res.fun)) * ftol * hess_inv_i)
        tmp_i[i] = 0.0
        logger.info('p{0} = {1:12.4e} ± {2:.1e}'.format(i, res.x[i], sd_i))
        standard_deviations[i] = sd_i
    return standard_deviations

def run_single_fit_function(up, 
                            fit, 
                            intensities, 
                            fit_results, 
                            x_spectrum_fit, 
                            peak_picking_data, 
                            scaling_factor,
                            use_previous_fit,
                            writing_to_file=True,
                            offset=False
                            ):

    d_id, initial_fit_values, bounds_fit, name_parameters = get_fitting_parameters(peak_picking_data, x_spectrum_fit, scaling_factor, offset=offset)
    if use_previous_fit :
        initial_fit_values = list(fit_results.iloc[fit[1]-1 if up else fit[1]+1].values)
        bounds_fit = refine_constraints(initial_fit_values, bounds_fit, name_parameters)
    
    try:
        intensities = intensities[fit[0],:]
        res_fit = minimize(
            fit_objective,
            x0=initial_fit_values,                
            bounds=bounds_fit,
            method='L-BFGS-B',
            options={'maxcor': 30},
            args=(x_spectrum_fit, intensities, d_id, scaling_factor, offset),
            )
        logger.info(res_fit)
        res_stats = compute_statistics(res_fit)
        logger.info(res_stats)

        if writing_to_file is False:
            return res_fit
        else:
            fit_results.loc[fit[1],:] = res_fit.x.tolist()

    except:
        logger.error('An unknown error has occured when fitting spectra: '+str(fit[1]))

def full_fitting_procedure(   
    intensities         =   'intensities',
    x_spec              =   'x_Spec',
    ref_spec            =   'ref_spec',
    peak_picking_data   =   'peak_picking_data',
    scaling_factor      =    None,
    spectra_to_fit      =   'spectra_to_fit',
    use_previous_fit    =   'use_previous_fit',
    offset=False
    ): 
    
    # Handling spectra list for multi-threading
    id_spec_part2 = [i for i in spectra_to_fit if i[0] < ref_spec]
    id_spec_part1 = [i for i in spectra_to_fit if i[0] > ref_spec]
    id_ref_spec = [i for i in spectra_to_fit if i[0] == ref_spec ]

    # Fitting the reference 1D spectrum -- This function can be used for 1D spectrum alone
    logger.info(f'Fitting Reference Spectrum (ExpNo {id_ref_spec[0][5]})')
    res_fit_reference_spectrum = run_single_fit_function(
        None, # No need of up or down here
        id_ref_spec[0],
        intensities,
        None,  
        x_spec, 
        peak_picking_data,  
        scaling_factor,
        False,
        writing_to_file=False,
        offset=offset
        ) 
    logger.info(f'Fitting Reference Spectrum (ExpNo {id_ref_spec[0][5]}) -- Complete')

    # Creation of the data frame containing fitting results
    fit_results_table = pd.DataFrame(
        index=[i[1] for i in spectra_to_fit],
        columns=np.arange(0,len(res_fit_reference_spectrum.x.tolist()),1)
            )
    # Filling the dataframe for the reference spectrum 
    fit_results_table.loc[id_ref_spec[0][1],:] = res_fit_reference_spectrum.x.tolist()

    root, close_button, progress_bars = nfui.init_progress_bar_windows(
        len_progresses = [len(id_spec_part1), len(id_spec_part2)],
        title='Fitting in progress...',
        progress_bar_label=['Spectra part 1','Spectra part 2']
        ) 
    n_spec = intensities.shape[0]

    if n_spec == 1:
        pass
    else:
        threads = []

        if len(id_spec_part1):
            logger.info(f'Fitting from ExpNo {id_spec_part1[0][5]} to {np.max(id_spec_part1[-1][5])}')
            threads.append(MyApp_Fitting(data={
                "up"                  : True,
                "spec_list"           : id_spec_part1,
                "intensities"         : intensities,
                "fit_results"         : fit_results_table,
                "x_spectrum_fit"      : x_spec,
                "peak_picking_data"   : peak_picking_data,
                "scaling_factor"      : scaling_factor,
                "use_previous_fit"    : use_previous_fit,
                "offset"              : offset
            },
            threads=threads,
            close_button=close_button,
            progressbar=progress_bars[0]
            ))
            logger.info(f'Fitting from ExpNo {id_spec_part1[0][5]} to {id_spec_part1[-1][5]} -- Complete')
        else:
            logger.info(f'No spectra to fit above the reference spectrum') 

        if len(id_spec_part2):
            logger.info(f'Fitting from ExpNo {id_spec_part2[-1][5]} to {id_spec_part2[0][5]}')
            threads.append(MyApp_Fitting(data={
                "up"                  : False,
                "spec_list"           : id_spec_part2[::-1],
                "intensities"         : intensities,
                "fit_results"         : fit_results_table,
                "x_spectrum_fit"      : x_spec,
                "peak_picking_data"   : peak_picking_data,
                "scaling_factor"      : scaling_factor,
                "use_previous_fit"    : use_previous_fit,
                "offset"              : offset
            },
            threads=threads,
            close_button=close_button,
            progressbar=progress_bars[1]
            ))
            logger.info(f'Fitting from ExpNo {id_spec_part2[-1][5]} to {id_spec_part2[0][5]} -- Complete')
        else:
            logger.info(f'No spectra to fit below the reference spectrum') 

        root.mainloop()
    
    return fit_results_table

class MyApp_Fitting(threading.Thread):

    def __init__(self, data, threads, close_button, progressbar):
        self.finished = False
        self.threads = threads
        self.data = data
        self.close_button = close_button
        # self.progress_label = progress_label
        self.progressbar = progressbar
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        spec_list = self.data.pop("spec_list")
        for fit in spec_list:
            self.progressbar["value"] += 1
            run_single_fit_function(fit=fit, **self.data)
        self.finished = True
        finished = True
        for thread in self.threads:
            finished = thread.finished if thread.finished == False else finished
        if finished:
            self.close_button.invoke()