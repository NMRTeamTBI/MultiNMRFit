import multinmrfit as nf
import multinmrfit.utils_nmrdata as nfu
import multinmrfit.fitting as nff
import numpy as np
import os
import pandas as pd
import logging
import json

logger = logging.getLogger(__name__)

################################################################
# Loading Raw Data 
################################################################

def run_analysis(user_input, gui=False):
    Analysis_Type = user_input['analysis_type']
    logger.info('Test')
    ######################################################
    ##################### Read and Load Data #############
    ######################################################
    if Analysis_Type in ['Pseudo2D','1D']:
        [data_all, dic_all, x_ppm_all] = nfu.Read_Raw_NMR_Data_Bruker(
                path_nmr_data   =   os.path.join(user_input['data_path'],user_input['data_folder']),
                expno_data      =   user_input['data_exp_no'],
                procno_data     =   user_input['data_proc_no']
        )
        Exp_List = None
    elif Analysis_Type in ['1D_Series']:
        Raw_y_Data = []
        Raw_x_Data = []
        Exp_List = user_input['data_exp_no']
        for n in Exp_List:
            [data, diC, x_ppm] = nfu.Read_Raw_NMR_Data_Bruker(
                    path_nmr_data   =   os.path.join(user_input['data_path'],user_input['data_folder']),
                    expno_data      =   n,
                    procno_data     =   user_input['data_proc_no']
            )       
            
            Raw_x_Data.append(x_ppm)  
            Raw_y_Data.append(data)  

        x_ppm_all = np.array(Raw_x_Data)
        data_all = np.array(Raw_y_Data)
    else:
        raise ValueError("Wrong type of experiment in 'Analysis_Type' (expected 'Pseudo2D','1D' or '1D_Series', got '{}').".format(Analysis_Type))
    #-----------------------------------------------------#    

    ######################################################
    #Extract data within the region selected by the user##
    ######################################################
    [_Ext_data_, _Ext_x_ppm_] = nfu.Extract_Data(
        data     = data_all,
        x_ppm    = x_ppm_all,
        x_lim    = [user_input['spectral_limits'][0],user_input['spectral_limits'][1]]
    )
    #-----------------------------------------------------#   

    ######################################################
    ###########Extract the reference spectrum#############
    ######################################################
    if Analysis_Type == 'Pseudo2D':
        y_Spec_init_ = _Ext_data_[int(user_input['reference_spectrum' ])-1,:]
        x_Spec_init_ = _Ext_x_ppm_
    elif Analysis_Type == '1D_Series':
        y_Spec_init_ = _Ext_data_[int(user_input['reference_spectrum' ])-1,:]
        x_Spec_init_ = _Ext_x_ppm_[int(user_input['reference_spectrum' ])-1,:]
    elif Analysis_Type == '1D':
        y_Spec_init_ = _Ext_data_
        x_Spec_init_ = _Ext_x_ppm_
    #-----------------------------------------------------#   

    ######################################################
    ####################Peak Picking######################
    ######################################################
    Peak_Picking = nfu.Peak_Picking_1D(
        x_data          =   x_Spec_init_, 
        y_data          =   y_Spec_init_, 
        threshold       =   user_input['threshold'],
    )
    #-----------------------------------------------------#   

    ######################################################
    #############Manual Check of Peak Picking#############
    ######################################################

    peak_picking_data = nfu.sort_peak_picking_data(Peak_Picking, 10)

    fig_peak_picking_region, color_list = nf.ui.plot_picking_data(
        x_Spec_init_, 
        y_Spec_init_, 
        user_input['threshold'], 
        peak_picking_data
    )

    new_th, user_picked_data = nf.ui.run_user_clustering(
        fig_peak_picking_region,
        color_list,
        user_input['threshold'],
        peak_picking_data
    )

    check_for_nt = new_th.isnull().values.any()

 
    while check_for_nt == False:
        new_th = new_th.apply(pd.to_numeric, errors='coerce')
        pp_t = new_th.nt.values[0]

        Peak_Picking = nfu.Peak_Picking_1D(
            x_data          =   x_Spec_init_, 
            y_data          =   y_Spec_init_, 
            threshold       =   pp_t,
        )

        fig_peak_picking_region, color_list = nf.ui.plot_picking_data(
            x_Spec_init_, 
            y_Spec_init_, 
            pp_t, 
            Peak_Picking
        )

        peak_picking_data = nfu.sort_peak_picking_data(Peak_Picking, 10)
        new_th, user_picked_data = nf.ui.run_user_clustering(
            fig_peak_picking_region,
            color_list,
            pp_t,
            peak_picking_data
        )
        check_for_nt = new_th.isnull().values.any()
    
    #print(user_picked_data)
    #print(user_picked_data["Selection"].values)
    #exit()
    user_picked_data = user_picked_data[user_picked_data["Selection"].values]
    #print(user_picked_data)
    #exit()
    scaling_factor = user_picked_data.Peak_Amp.mean()
    #cluster_list =  user_picked_data.Cluster.unique()
    #-----------------------------------------------------#   
    ######################################################
    #######################Fitting########################
    ######################################################
    if Analysis_Type in ['1D','1D_Series','Pseudo2D']:
        Fit_results = nff.Pseudo2D_PeakFitting(
                    Intensities  =   _Ext_data_,
                    x_Spec       =   x_Spec_init_,
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
        Int_Pseudo_2D_Data = _Ext_data_,
        x_ppm = x_Spec_init_,
        Peak_Picking_data= user_picked_data,
        scaling_factor=scaling_factor,
        gui=gui,
        id_spectra=Exp_List
    )
    print('Full Analysis is done')
    print('#--------#')  
    print('##########')
    return Peak_Picking


#analysis_Pseudo2D(Inputs_dic)
#exit()




