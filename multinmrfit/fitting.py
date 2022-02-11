from tkinter.constants import ANCHOR
import warnings
import logging
import random

warnings.filterwarnings('ignore')
import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd
from scipy.optimize import minimize

import multinmrfit.multiplets as nfm
import multinmrfit.ui as nfui
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

def Initial_Values(
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
        d_id[n] = (_multiplet_type_function, [len(ini_params),len(ini_params)+len(Init_Val)])
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
    peakpicking_data,
    y_fit_,
    d_id,
    scaling_factor
    ):
    sim_intensity = simulate_data(x_fit_,fit_par, d_id, scaling_factor)
    rmsd = np.sqrt(np.mean((sim_intensity - y_fit_)**2))
    return rmsd

def Fitting_Function(
    x_fit_,
    peakpicking_data,
    y_fit_,
    scaling_factor,
    Initial_Val=None):

    if Initial_Val is not None:        
        init_ = Initial_Val
    else:
        init_= Initial_Values(peakpicking_data, x_fit_, scaling_factor)[1]
    #bounds_fit_ = Initial_Values(peakpicking_data, x_fit_, d_clustering, d_mapping)[2]
    d_id, _, bounds_fit_ = Initial_Values(peakpicking_data, x_fit_, scaling_factor)
    res_fit = minimize(
                fit_objective,
                x0=init_,                
                bounds=bounds_fit_,
                method='L-BFGS-B',
                #options={'ftol': 1e-6},#,'maxiter':0},
                args=(x_fit_,peakpicking_data,y_fit_, d_id, scaling_factor),
    )
    return res_fit

def run_single_fit_function(up, fit, intensities, fit_results, x_Spec, peak_picking_data, scaling_factor, analysis_type, spec_list,use_previous_fit=False):
    print( fit_results)
    Initial_Fit_Values = list(fit_results.iloc[fit[1]-1 if up else fit[1]+1].values) if use_previous_fit else None

    try:

        _1D_Fit_ = Fitting_Function(
                    x_Spec,
                    peak_picking_data,
                    intensities[fit[0],:],
                    scaling_factor,
                    Initial_Fit_Values) 
        print(_1D_Fit_.x.tolist())
        fit_results.loc[fit[1],:] = _1D_Fit_.x.tolist()
    
    except:
        logger.error('Error: '+str(fit[1]))

def Full_Fitting_Function(   
    intensities         =   'intensities',
    x_Spec              =   'x_Spec',
    ref_spec            =   'ref_spec',
    peak_picking_data   =   'peak_picking_data',
    scaling_factor      =    None,
    analysis_type       =   'analysis_type',
    spectra_to_fit      =   'spectra_to_fit',
    use_previous_fit = True
    ): 

    n_spec = 1 if intensities.ndim == 1 else intensities.shape[0]
    
    #if analysis_type == 'Pseudo2D':
    #    id_spec_part2 = [spectra_to_fit[i] for i,j in enumerate(spectra_to_fit) if j < ref_spec]
    #    id_spec_part1 = [spectra_to_fit[i] for i,j in enumerate(spectra_to_fit) if j > ref_spec]
    #elif analysis_type == '1D_Series':
    #    id_spec_part2 = [i for i,j in enumerate(spectra_to_fit) if i < ref_spec]
    #    id_spec_part1 = [i for i,j in enumerate(spectra_to_fit) if i > ref_spec]
    #    id_all        = id_spec_part2+[ref_spec]+id_spec_part1

    id_spec_part2 = [i for i in spectra_to_fit if i[0] < ref_spec]
    id_spec_part1 = [i for i in spectra_to_fit if i[0] > ref_spec]
    id_ref_spec = [i for i in spectra_to_fit if i[0] == ref_spec ]
    id_all        = id_spec_part2+id_ref_spec+id_spec_part1

    y_Spec_init_ = intensities if intensities.ndim == 1 else intensities[ref_spec,:]

    #Fitting of the reference 1D spectrum -- This function can be used for 1D spectrum alone
    logger.info(f'Fitting Reference Spectrum (ExpNo {ref_spec})')

    Initial_Fit_ = Fitting_Function(x_Spec, peak_picking_data, y_Spec_init_, scaling_factor)

    logger.info(f'Fitting Reference Spectrum (ExpNo {ref_spec}) -- Complete')

    Fit_results = pd.DataFrame(
        index=[i[1] for i in spectra_to_fit],
        columns=np.arange(0,len(Initial_Fit_.x.tolist()),1)
            )
    if intensities.ndim == 1:
        Fit_results.loc[0,:] = Initial_Fit_.x.tolist()

    root, close_button, progress_bars = nfui.init_progress_bar_windows(
        len_progresses = [len(id_spec_part1), len(id_spec_part2)],
        title='Data Fitting',
        progress_bar_label=['Spectra part 1','Spectra part 2']
        ) 
    
    print("test")
    print(f"spectra to fit: {spectra_to_fit}")
    print(f"id_spec_part2: {id_spec_part2}")
    print(f"id_spec_part1: {id_spec_part1}")
    print(f"id_ref_spec: {id_ref_spec}")
    print(f"id_all: {id_all}")
    print(f"ref_spec: {ref_spec}")
    if intensities.ndim != 1:
        Fit_results.loc[id_ref_spec[0][1],:] = Initial_Fit_.x.tolist()

        threads = []
        print('####',ref_spec,spectra_to_fit[0][1])
        if len(id_spec_part1):
            print('Hello')
            logger.info(f'Fitting from ExpNo {ref_spec} to {np.max(id_spec_part1)}')
            threads.append(nfui.MyApp_Fitting(data={
                "up"                  : True,
                "spec_list"           : id_spec_part1,
                "intensities"         : intensities,
                "fit_results"         : Fit_results,
                "x_Spec"              : x_Spec,
                "peak_picking_data"   : peak_picking_data,
                "analysis_type"       : analysis_type,
                "scaling_factor"      : scaling_factor,
                "use_previous_fit"    : use_previous_fit
            },
            threads=threads,
            close_button=close_button,
            progressbar=progress_bars[0]
            ))
            logger.info(f'Fitting from ExpNo {ref_spec} to {np.max(id_spec_part1)} -- Complete')
        # elif:
        #     logger.info(f'No fitting above the reference spectrum') 
        if len(id_spec_part2):
            print('Hello -- 2')

            logger.info(f'Fitting from ExpNo {np.min(id_spec_part2)} to {np.max(id_spec_part2)}')
            threads.append(nfui.MyApp_Fitting(data={
                "up"                  : False,
                "spec_list"           : id_spec_part2[::-1],
                "intensities"         : intensities,
                "fit_results"         : Fit_results,
                "x_Spec"              : x_Spec,
                "peak_picking_data"   : peak_picking_data,
                "analysis_type"       : analysis_type,
                "scaling_factor"      : scaling_factor,
                "use_previous_fit"    : use_previous_fit
            },
            threads=threads,
            close_button=close_button,
            progressbar=progress_bars[1]
            ))
            logger.info(f'Fitting from ExpNo {np.min(id_spec_part2)} to {np.max(id_spec_part2)} -- Complete')
        
        root.mainloop()
    return Fit_results


