# System Libraries
import os
import logging
import json
import sys
import warnings
warnings.filterwarnings('ignore')
import tkinter as tk
# Other libs
import numpy as np
import pandas as pd

# Own Libs
import multinmrfit as nf
import multinmrfit.ui_new as nui
import multinmrfit.io as nio
import multinmrfit.utils_nmrdata as nfu
import multinmrfit.fitting as nff

# Import plot libraries
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

logger = logging.getLogger(__name__)

################################################################
# Loading Raw Data 
################################################################


def main():
    if not len(sys.argv) == 2:
        print('gui')
        app = nui.App(user_input=nio.create_user_input())
        app.start()
    else:
        print('cli')
        user_input = nio.load_config_file(None,config_file_path=sys.argv[1]) 
        user_input = nio.check_input_file(user_input,None)       
        run_analysis(user_input,None)

def prepare_data(user_input):
    ######################################################
    ##################### Read and Load Data #############
    ######################################################
    intensities, x_ppm, experiments_list = nfu.retrieve_nmr_data(user_input) 
    logger.info('Loading -- Complete')
    #-----------------------------------------------------#    

    ######################################################
    #Extract data within the region selected by the user##
    ######################################################
    logger.info('Extraction of NMR Data')
    intensities, x_ppm = nfu.Extract_Data(
        data     = intensities,
        x_ppm    = x_ppm,
        x_lim    = [user_input['spectral_limits'][0],user_input['spectral_limits'][1]]
    )
    logger.info('Extraction -- Complete')
    #-----------------------------------------------------#
    # 
    if user_input['analysis_type'] == 'Pseudo2D':
        idx_ref = int(user_input['reference_spectrum' ]) - 1  
    else:            
        idx_ref = user_input['data_exp_no'].index(int(user_input['reference_spectrum' ]))

    ######################################################
    ###########Extract the reference spectrum#############
    ######################################################
    if user_input['analysis_type'] == 'Pseudo2D':
        intensities_reference_spectrum = intensities[idx_ref,:]
        x_ppm_reference_spectrum = x_ppm
    elif user_input['analysis_type'] == '1D_Series':
        intensities_reference_spectrum = intensities[idx_ref,:]
        x_ppm_reference_spectrum = x_ppm[idx_ref,:]
    elif user_input['analysis_type'] == '1D':
        intensities_reference_spectrum = intensities
        x_ppm_reference_spectrum = x_ppm
    #-----------------------------------------------------#   

    ######################################################
    ####################Peak Picking######################
    ######################################################

    threshold = user_input['threshold']

    while threshold:

        peak_picking = nfu.Peak_Picking_1D(
            x_data          =   x_ppm_reference_spectrum, 
            y_data          =   intensities_reference_spectrum, 
            threshold       =   threshold,
        )

        peak_picking_data = nfu.sort_peak_picking_data(peak_picking, 10)
        
        fig_peak_picking_region, color_list = nui.plot_picking_data(
            x_ppm_reference_spectrum, 
            intensities_reference_spectrum, 
            threshold, 
            peak_picking_data
            )

        threshold, user_picked_data = nui.run_user_clustering(
            fig_peak_picking_region,
            color_list,
            threshold,
            peak_picking_data
        )

    user_picked_data = user_picked_data[user_picked_data["Selection"].values]

    scaling_factor = user_picked_data.Peak_Intensity.mean()

    # (id, expno, procno, rowno, output_name)
    if user_input['analysis_type'] == "Pseudo2D" : 
        if not len(user_input.get('data_row_no',[])):
            user_input['data_row_no'] = np.arange(1,len(intensities)+1,1)
            #spectra_to_fit = list(np.arange(0,len(intensities),1))
        #    spectra_to_fit = [(user_input['data_exp_no'][0], user_input['data_proc_no'], i, i) for i in np.arange(0,len(intensities),1)]
        #else:
        #    #spectra_to_fit = [int(i)-1 for i in user_input['data_row_no']]
        spectra_to_fit = [(j-1, i, user_input['data_exp_no'][0], user_input['data_proc_no'], j, j) for i,j in enumerate(user_input['data_row_no'])]
    elif user_input['analysis_type'] == '1D_Series':
            spectra_to_fit = [(i, i, j, user_input['data_proc_no'], 1, j) for i, j in enumerate(user_input['data_exp_no'])]

    return spectra_to_fit, intensities, x_ppm_reference_spectrum, idx_ref, user_picked_data, scaling_factor

def run_analysis(user_input, gui=False):
    logger.info('Loading NMR Data')

    spectra_to_fit, intensities, x_ppm_reference_spectrum, idx_ref, user_picked_data, scaling_factor = prepare_data(user_input)

    #-----------------------------------------------------#   
    ######################################################
    #######################Fitting########################
    ######################################################
    fit_results_table = nff.full_fitting_procedure(
        intensities         =   intensities,
        x_spec              =   x_ppm_reference_spectrum,
        ref_spec            =   idx_ref,
        peak_picking_data   =   user_picked_data,
        scaling_factor      =   scaling_factor,
        spectra_to_fit      =   spectra_to_fit
        
    )
    #-----------------------------------------------------#   
    ######################################################
    #######################Output#########################
    ######################################################
    nio.save_output_data(
        user_input          ,
        fit_results_table   ,
        intensities         ,
        x_ppm_reference_spectrum,
        spectra_to_fit,
        user_picked_data,
        scaling_factor

    )
    logger.info('Full Analysis is complete')
    logger.info('####')

    return 
