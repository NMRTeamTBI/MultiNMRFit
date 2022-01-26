# System Libraries
import os
import logging
import json
import sys
import warnings
warnings.filterwarnings('ignore')

# Other libs
import numpy as np
import pandas as pd

# Own Libs
import multinmrfit as nf
import multinmrfit.ui as nui

import multinmrfit.utils_nmrdata as nfu
import multinmrfit.fitting as nff

logger = logging.getLogger(__name__)

################################################################
# Loading Raw Data 
################################################################

def main():
    if not len(sys.argv) == 2:
        nui.start_gui()
    else:
        user_input = nui.load_config_file(config_file_path=sys.argv[1])
        nui.launch_analysis(user_input)
    
def run_analysis(user_input, gui=False):
    logger.info('Loading NMR Data')
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

        fig_peak_picking_region, color_list = nf.ui.plot_picking_data(
            x_ppm_reference_spectrum, 
            intensities_reference_spectrum, 
            threshold, 
            peak_picking_data
        )

        threshold, user_picked_data = nf.ui.run_user_clustering(
            fig_peak_picking_region,
            color_list,
            threshold,
            peak_picking_data
        )

    user_picked_data = user_picked_data[user_picked_data["Selection"].values]

    scaling_factor = user_picked_data.Peak_Intensity.mean()
    #-----------------------------------------------------#   
    ######################################################
    #######################Fitting########################
    ######################################################
    fit_results = nff.Full_Fitting_Function(
        intensities         =   intensities,
        x_Spec              =   x_ppm_reference_spectrum,
        ref_spec            =   idx_ref,#user_input['reference_spectrum'],
        peak_picking_data   =   user_picked_data,
        scaling_factor      =   scaling_factor,
        analysis_type       =   user_input['analysis_type']
        
    )
    #-----------------------------------------------------#   
    ######################################################
    #######################Output#########################
    ######################################################
    
    nf.ui.save_output_data(
        output_path         =   user_input['output_path'],
        output_folder       =   user_input['output_folder'],
        output_name         =   user_input['output_name'],
        fit_results         =   fit_results,
        intensities         =   intensities,
        x_scale             =   x_ppm_reference_spectrum,
        Peak_Picking_data   =   user_picked_data,
        scaling_factor      =   scaling_factor,
        id_spectra          =   experiments_list
    )
    logger.info('Full Analysis is complete')
    logger.info('####')

    return 
