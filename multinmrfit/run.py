# System Libraries
import os
import logging
import json
import sys

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
    logger.info('Loading Complete')
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
    logger.info('Extraction Complete')
    #-----------------------------------------------------#   

    ######################################################
    ###########Extract the reference spectrum#############
    ######################################################
    if user_input['analysis_type'] == 'Pseudo2D':
        intensities_reference_spectrum = intensities[int(user_input['reference_spectrum' ])-1,:]
        x_ppm_reference_spectrum = x_ppm
    elif user_input['analysis_type'] == '1D_Series':
        intensities_reference_spectrum = intensities[int(user_input['reference_spectrum' ])-1,:]
        x_ppm_reference_spectrum = x_ppm[int(user_input['reference_spectrum' ])-1,:]
    elif user_input['analysis_type'] == '1D':
        intensities_reference_spectrum = intensities
        x_ppm_reference_spectrum = x_ppm
    #-----------------------------------------------------#   

    ######################################################
    ####################Peak Picking######################
    ######################################################
    check_for_refreshed_threshold = False

    Peak_Picking = nfu.Peak_Picking_1D(
        x_data          =   x_ppm_reference_spectrum, 
        y_data          =   intensities_reference_spectrum, 
        threshold       =   user_input['threshold']
    )

    peak_picking_data = nfu.sort_peak_picking_data(Peak_Picking, 10)

    fig_peak_picking_region, color_list = nf.ui.plot_picking_data(
        x_ppm_reference_spectrum, 
        intensities_reference_spectrum, 
        user_input['threshold'], 
        peak_picking_data
    )

    refreshed_threshold, user_picked_data = nf.ui.run_user_clustering(
        fig_peak_picking_region,
        color_list,
        user_input['threshold'],
        peak_picking_data
    )

    while refreshed_threshold:
        threshold = refreshed_threshold

        Peak_Picking = nfu.Peak_Picking_1D(
            x_data          =   x_ppm_reference_spectrum, 
            y_data          =   intensities_reference_spectrum, 
            threshold       =   threshold,
        )

        fig_peak_picking_region, color_list = nf.ui.plot_picking_data(
            x_ppm_reference_spectrum, 
            intensities_reference_spectrum, 
            threshold, 
            Peak_Picking
        )

        peak_picking_data = nfu.sort_peak_picking_data(Peak_Picking, 10)
        refreshed_threshold, user_picked_data = nf.ui.run_user_clustering(
            fig_peak_picking_region,
            color_list,
            threshold,
            peak_picking_data
        )
    
    #print(user_picked_data)
    #print(user_picked_data["Selection"].values)
    #exit()
    user_picked_data = user_picked_data[user_picked_data["Selection"].values]
    #print(user_picked_data)
    #exit()
    scaling_factor = user_picked_data.Peak_Intensity.mean()
    #cluster_list =  user_picked_data.Cluster.unique()
    #-----------------------------------------------------#   
    ######################################################
    #######################Fitting########################
    ######################################################
    if user_input['analysis_type'] in ['1D','1D_Series','Pseudo2D']:
        Fit_results = nff.Pseudo2D_PeakFitting(
                    Intensities  =   intensities,
                    x_Spec       =   x_ppm_reference_spectrum,
                    ref_spec     =   user_input['reference_spectrum'],
                    peak_picking_data = user_picked_data,
                    scaling_factor=scaling_factor,
                    gui=gui
            )

    #-----------------------------------------------------#   
    ######################################################
    #######################Output#########################
    ######################################################
    nf.ui.Plot_All_Spectrum(
        pdf_path = user_input['output_path'],
        pdf_folder = user_input['output_folder'],
        pdf_name = user_input['output_name'],
        Fit_results= Fit_results,
        Int_Pseudo_2D_Data = intensities,
        x_ppm = x_ppm_reference_spectrum,
        Peak_Picking_data= user_picked_data,
        scaling_factor=scaling_factor,
        gui=gui,
        id_spectra=experiments_list
    )
    print('Full Analysis is done')
    print('#--------#')  
    print('##########')
    return Peak_Picking


#analysis_Pseudo2D(Inputs_dic)
#exit()




