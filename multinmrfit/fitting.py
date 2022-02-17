from tkinter.constants import ANCHOR
import warnings
import logging
import random
import threading

warnings.filterwarnings('ignore')
import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd
from scipy.optimize import minimize

import multinmrfit.multiplets as nfm
import multinmrfit.ui_new as nfui
import matplotlib
import matplotlib.pyplot as plt
logger = logging.getLogger(__name__)
# Set Initial Values for fitting

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
    scaling_factor
    ):
    ini_params, ini_constraints = [], []
    cluster_list =  peakpicking_data.Cluster.unique()
    d_id = {k:[] for k in cluster_list}
    d_mapping, d_clustering, _ = nfm.mapping_multiplets()
    Initial_offset = 0

    for n in cluster_list:
        _cluster_ = peakpicking_data.loc[peakpicking_data.Cluster==n]
        id_cluster = str(len(_cluster_)) + "".join(i for i in set(_cluster_.Options.values.tolist()))
        _multiplet_type_ = d_clustering[id_cluster]
        _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
        Init_Val = nfm.Peak_Initialisation(_multiplet_type_,Peak_Picking_Results=_cluster_,scaling_factor=scaling_factor)
        #Init_Cons = Constraints_Initialisation(_multiplet_type_)
        d_id[n] = (_multiplet_type_function, [len(ini_params),len(ini_params)+len(Init_Val)],_multiplet_type_)
        ini_params.extend(Init_Val)
        upd_cons = update_resolution(d_mapping[_multiplet_type_]["constraints"], x_fit_)
        upd_cons = update_position(d_mapping[_multiplet_type_]["constraints"], x_fit_)
        ini_constraints.extend(upd_cons)
    ini_params.extend([Initial_offset])
    ini_constraints.extend([(-0.1, 0.1)])
    return d_id, ini_params, ini_constraints

def simulate_data(x_fit_, fit_par, d_id, scaling_factor):
    # initialize simulated spectrum at 0
    sim_intensity = np.zeros(len(x_fit_))
    # add subspectrum of each spin system
    for n in d_id.keys():
        # get parameters of spin system
        params = fit_par[d_id[n][1][0]:d_id[n][1][1]]
        # simulate and add corresponding subspectrum
        sim_intensity += d_id[n][0](x_fit_, *params)
    # add offset (corresponds to 0-order baseline correction)
    sim_intensity += fit_par[-1]
    # multiply by scaling factor (required for stable minimization)
    sim_intensity *= scaling_factor
    return sim_intensity

def fit_objective(
    fit_par,
    x_fit_,
    y_fit_,
    d_id,
    scaling_factor
    ):
    sim_intensity = simulate_data(x_fit_,fit_par, d_id, scaling_factor)
    rmsd = np.sqrt(np.mean((sim_intensity - y_fit_)**2))
    return rmsd

def run_single_fit_function(up, 
                            fit, 
                            intensities, 
                            fit_results, 
                            x_spectrum_fit, 
                            peak_picking_data, 
                            scaling_factor,
                            use_previous_fit,
                            writing_to_file=True
                            ):

    # up is usef for the multithreading 
    if use_previous_fit :
        initial_fit_values = list(fit_results.iloc[fit[1]-1 if up else fit[1]+1].values)
    else:
        initial_fit_values= get_fitting_parameters(peak_picking_data, x_spectrum_fit, scaling_factor)[1]
    d_id, _, bounds_fit = get_fitting_parameters(peak_picking_data, x_spectrum_fit, scaling_factor)


    try:
        res_fit = minimize(
            fit_objective,
            x0=initial_fit_values,                
            bounds=bounds_fit,
            method='L-BFGS-B',
            #options={'ftol': 1e-6},#,'maxiter':0},
            args=(x_spectrum_fit,intensities[fit[0],:], d_id, scaling_factor),
            )

        if writing_to_file is False:
            return res_fit
        else:
            fit_results.loc[fit[1],:] = res_fit.x.tolist()
    
    except:
        logger.error('Error: '+str(fit[1]))

def full_fitting_procedure(   
    intensities         =   'intensities',
    x_spec              =   'x_Spec',
    ref_spec            =   'ref_spec',
    peak_picking_data   =   'peak_picking_data',
    scaling_factor      =    None,
    spectra_to_fit      =   'spectra_to_fit',
    use_previous_fit    =   'use_previous_fit'
    ): 
    
    # Handling spectra list for multi-threading
    id_spec_part2 = [i for i in spectra_to_fit if i[0] < ref_spec]
    id_spec_part1 = [i for i in spectra_to_fit if i[0] > ref_spec]
    id_ref_spec = [i for i in spectra_to_fit if i[0] == ref_spec ]

    #Fitting of the reference 1D spectrum -- This function can be used for 1D spectrum alone
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
        writing_to_file=False
        ) 
    logger.info(f'Fitting Reference Spectrum (ExpNo {id_ref_spec[0][5]}) -- Complete')

    #Creation of the data frame containing all the results from the fitting
    fit_results_table = pd.DataFrame(
        index=[i[1] for i in spectra_to_fit],
        columns=np.arange(0,len(res_fit_reference_spectrum.x.tolist()),1)
            )
    # Filling the dataframe for the reference spectrum 
    fit_results_table.loc[id_ref_spec[0][1],:] = res_fit_reference_spectrum.x.tolist()

    root, close_button, progress_bars = nfui.init_progress_bar_windows(
        len_progresses = [len(id_spec_part1), len(id_spec_part2)],
        title='Data Fitting',
        progress_bar_label=['Spectra part 1','Spectra part 2']
        ) 

    if intensities.ndim == 1:
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
                "use_previous_fit"    : use_previous_fit
            },
            threads=threads,
            close_button=close_button,
            progressbar=progress_bars[0]
            ))
            logger.info(f'Fitting from ExpNo {id_spec_part1[0][5]} to {id_spec_part1[-1][5]} -- Complete')
        else:
            logger.info(f'No fitting above the reference spectrum') 

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
                "use_previous_fit"    : use_previous_fit
            },
            threads=threads,
            close_button=close_button,
            progressbar=progress_bars[1]
            ))
            logger.info(f'Fitting from ExpNo {id_spec_part2[-1][5]} to {id_spec_part2[0][5]} -- Complete')
        else:
            logger.info(f'No fitting below the reference spectrum') 

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