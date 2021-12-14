import nmrfit as nf
import nmrfit.utils_nmrdata as nfu
import nmrfit.fitting as nff
import numpy as np
import sys
import os
import pandas as pd



################################################################
# Loading Raw Data 
################################################################
# if Analysis_Type not in ['1D_Series','Pseudo2D','1D']:
#     exit()

def run_analysis(imputs_dic, gui=False):

    Analysis_Type = imputs_dic['Data_Type']

    ######################################################
    ##################### Read and Load Data #############
    ######################################################
    if Analysis_Type in ['Pseudo2D','1D']:
        [data_all, dic_all, x_ppm_all] = nfu.Read_Raw_NMR_Data_Bruker(
                path_nmr_data   =   os.path.join(imputs_dic['Data_Path'],imputs_dic['Data_Folder']),
                expno_data      =   imputs_dic['ExpNo'],
                procno_data     =   imputs_dic['ProcNo']
        )
        Exp_List = None
    elif Analysis_Type in ['1D_Series']:
        Raw_y_Data = []
        Raw_x_Data = []
        Exp_List_tmp = [i for i in imputs_dic['ExpNo'].split(',')]
        Exp_List = []
        for i in Exp_List_tmp:
            if "-" in i:
                spectra = i.split('-')
                Exp_List += range(int(spectra[0]), int(spectra[1])+1)
            else:
                Exp_List.append(int(i))
        for n in Exp_List:
            [data, diC, x_ppm] = nfu.Read_Raw_NMR_Data_Bruker(
                    path_nmr_data   =   os.path.join(imputs_dic['Data_Path'],imputs_dic['Data_Folder']),
                    expno_data      =   n,
                    procno_data     =   imputs_dic['ProcNo']
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
        x_lim    = [imputs_dic['Spec_Lim'][0],imputs_dic['Spec_Lim'][1]]
    )
    #-----------------------------------------------------#   

    ######################################################
    ###########Extract the reference spectrum#############
    ######################################################
    if Analysis_Type == 'Pseudo2D':
        y_Spec_init_ = _Ext_data_[int(imputs_dic['Ref_Spec' ])-1,:]
        x_Spec_init_ = _Ext_x_ppm_
    elif Analysis_Type == '1D_Series':
        y_Spec_init_ = _Ext_data_[int(imputs_dic['Ref_Spec' ])-1,:]
        x_Spec_init_ = _Ext_x_ppm_[int(imputs_dic['Ref_Spec' ])-1,:]
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
    threshold       =   imputs_dic['Threshold'],
    )
    #-----------------------------------------------------#   

    ######################################################
    #############Manual Check of Peak Picking#############
    ######################################################
    #exit()
    new_th, pp_res_Sel = nf.ui.gui_peak_picking(x_Spec_init_,y_Spec_init_,imputs_dic['Threshold'],Peak_Picking)
    check_for_nt = new_th.isnull().values.any()
    while check_for_nt == False:
        new_th = new_th.apply(pd.to_numeric, errors='coerce')
        pp_t = new_th.nt.values[0]

        Peak_Picking = nfu.Peak_Picking_1D(
            x_data          =   x_Spec_init_, 
            y_data          =   y_Spec_init_, 
            threshold       =   pp_t,
        )
        
        new_th, pp_res_Sel = nf.ui.gui_peak_picking(x_Spec_init_,y_Spec_init_,pp_t,Peak_Picking)
        check_for_nt = new_th.isnull().values.any()
        if check_for_nt == True:
            break
    #print(pp_res_Sel)
    #print(pp_res_Sel["Selection"].values)
    #exit()
    pp_res_Sel = pp_res_Sel[pp_res_Sel["Selection"].values]
    #print(pp_res_Sel)
    #exit()
    scaling_factor = pp_res_Sel.Peak_Amp.mean()
    #cluster_list =  pp_res_Sel.Cluster.unique()
    #-----------------------------------------------------#   
    ######################################################
    #######################Fitting########################
    ######################################################
    if Analysis_Type in ['1D','1D_Series','Pseudo2D']:
        Fit_results = nff.Pseudo2D_PeakFitting(
                    Intensities  =   _Ext_data_,
                    x_Spec       =   x_Spec_init_,
                    ref_spec     =   imputs_dic['Ref_Spec'],
                    peak_picking_data = pp_res_Sel,
                    scaling_factor=scaling_factor,
                    gui=gui
            )

    #-----------------------------------------------------#   
    ######################################################
    #######################Output#########################
    ######################################################
    nf.ui.Plot_All_Spectrum(
        pdf_path = imputs_dic['pdf_path'],
        pdf_folder = imputs_dic['pdf_folder'],
        pdf_name = imputs_dic['pdf_name'],
        Fit_results= Fit_results,
        Int_Pseudo_2D_Data = _Ext_data_,
        x_ppm = x_Spec_init_,
        Peak_Picking_data= pp_res_Sel,
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




