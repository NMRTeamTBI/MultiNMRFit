# System Libraries
import logging
import sys
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd

# Own Libs
import multinmrfit.ui_new as nui
import multinmrfit.io as nio
import multinmrfit.utils_nmrdata as nfu
import multinmrfit.fitting as nff

logger = logging.getLogger(__name__)

################################################################
# Loading Raw Data 
################################################################


def main():
    if not len(sys.argv) == 2:
        app = nui.App(user_input=nio.create_user_input())
        app.start()
    else:
        user_input = nio.load_config_file(None,config_file_path=sys.argv[1]) 
        user_input = nio.check_input_file(user_input,None)       
        run_analysis(user_input,None)

# def prepare_data(user_input):
    # ######################################################
    # ##################### Read and Load Data #############
    # ######################################################
    # intensities, x_ppm = nfu.retrieve_nmr_data(user_input) 
    # logger.info('Loading -- Complete')
    # #-----------------------------------------------------#    

    # ######################################################
    # #Extract data within the region selected by the user##
    # ######################################################
    # logger.info('Extraction of NMR Data')
    # intensities, x_ppm = nfu.Extract_Data(
    #     data     = intensities,
    #     x_ppm    = x_ppm,
    #     x_lim    = [user_input['spectral_limits'][0],user_input['spectral_limits'][1]]
    # )
    # logger.info('Extraction -- Complete')
    # #-----------------------------------------------------#
    

    # if user_input['analysis_type'] == 'Pseudo2D':
    #     idx_ref = int(user_input['reference_spectrum' ]) - 1  
    # else:            
    #     idx_ref = user_input['data_exp_no'].index(int(user_input['reference_spectrum' ]))

    # ######################################################
    # ###########Extract the reference spectrum#############
    # ######################################################
    # if user_input['analysis_type'] == 'Pseudo2D':
    #     intensities_reference_spectrum = intensities[idx_ref,:]
    #     x_ppm_reference_spectrum = x_ppm
    # elif user_input['analysis_type'] == '1D_Series':
    #     intensities_reference_spectrum = intensities[idx_ref,:]
    #     x_ppm_reference_spectrum = x_ppm[idx_ref,:]
    # #-----------------------------------------------------#   

    # ######################################################
    # ##############Peak Picking/ Clustering################
    # ######################################################
    # threshold = user_input['threshold']

    # clustering_results = pd.DataFrame(columns=['Peak_Position','Peak_Intensity','Selection','Cluster','Options'])

    # print(clustering_results)
    # # app_clustering = nui.App_Clustering(
    # #     x_spec = x_ppm_reference_spectrum,
    # #     y_spec = intensities_reference_spectrum,
    # #     peak_picking_threshold = threshold,
    # #     clustering_table = clustering_results
    # #     )
    # exit()
    # app_clustering.start()

    # user_picked_data = clustering_results[clustering_results["Selection"].values]
    # user_picked_data = nfu.filter_multiple_clusters(user_picked_data)
    # scaling_factor = user_picked_data.Peak_Intensity.mean()

    # ######################################################
    # #Prepare spectral list with all required indices##
    # ######################################################
    # # (id, expno, procno, rowno, output_name)
    # if user_input['analysis_type'] == "Pseudo2D" : 
    #     if not len(user_input.get('option_data_row_no',[])):
    #         user_input['option_data_row_no'] = np.arange(1,len(intensities)+1,1)
    #     spectra_to_fit = [(j-1, i, user_input['data_exp_no'][0], user_input['data_proc_no'], j, j) for i,j in enumerate(user_input['option_data_row_no'])]
    # elif user_input['analysis_type'] == '1D_Series':
    #         spectra_to_fit = [(i, i, j, user_input['data_proc_no'], 1, j) for i, j in enumerate(user_input['data_exp_no'])]

    # ######################################################
    # #Check to use the previpous fit as initial values for fitting##
    # ######################################################
    # use_previous_fit = user_input['option_previous_fit']

    # offset = user_input['option_offset']
    # merged_pdf = user_input['option_merge_pdf']
    # return spectra_to_fit, intensities, x_ppm_reference_spectrum, idx_ref, user_picked_data, scaling_factor, use_previous_fit, offset, merged_pdf

# def run_analysis(user_input, gui=False):
#     logger.info('Loading NMR Data')

#     spectra_to_fit, intensities, x_ppm_reference_spectrum, idx_ref, user_picked_data, scaling_factor, use_previous_fit, offset, merged_pdf = prepare_data(user_input)
#     #-----------------------------------------------------#   
#     ######################################################
#     #######################Fitting########################
#     ######################################################
#     logger.info('Fit spectra')
#     fit_results_table = nff.full_fitting_procedure(
#         intensities         =   intensities,
#         x_spec              =   x_ppm_reference_spectrum,
#         ref_spec            =   idx_ref,
#         peak_picking_data   =   user_picked_data,
#         scaling_factor      =   scaling_factor,
#         spectra_to_fit      =   spectra_to_fit,
#         use_previous_fit    =   use_previous_fit,
#         offset              =   offset
#     )
#     #-----------------------------------------------------#   
#     ######################################################
#     #######################Output#########################
#     ######################################################
#     logger.info('Save results')
#     nio.save_output_data(
#         user_input          ,
#         fit_results_table   ,
#         intensities         ,
#         x_ppm_reference_spectrum,
#         spectra_to_fit,
#         user_picked_data,
#         scaling_factor,
#         offset=offset,
#         merged_pdf = merged_pdf
#     )
#     logger.info('Full Analysis is complete')
#     exit()


     
