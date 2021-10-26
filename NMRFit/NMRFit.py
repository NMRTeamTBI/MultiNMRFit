from Multiplets import *
from Interfaces import *
from Utils_nmrData import *
from Fitting import *

import sys


if sys.argv[1:]: # Start from command line; Do not use the user interface 
    config_file = sys.argv[1]
    User_Inputs = pd.read_csv(config_file,sep='\s+', header=1,names=['Var','User_Value']).set_index('Var')
    Inputs_dic = {
        'Data_Path'         :   User_Inputs.User_Value.Data_Path, 
        'Data_Folder'       :   User_Inputs.User_Value.Data_Folder, 
        'Data_Type'         :   User_Inputs.User_Value.Analysis_Type,
        'ExpNo'             :   int(User_Inputs.User_Value.Exp_Number) if len(User_Inputs.User_Value.Exp_Number) == 1 else User_Inputs.User_Value.Exp_Number, 
        'ProcNo'            :   int(User_Inputs.User_Value.ProcNo_Number), 
        'Ref_Spec'          :   int(User_Inputs.User_Value.Ref_Spectrum), 
        'Spec_Lim'          :   [float(i) for i in User_Inputs.User_Value.Specral_Region.split(',')],  
        'Threshold'         :   float(User_Inputs.User_Value.Threshold),       
        'pdf_path'          :   User_Inputs.User_Value.pdf_path,
        'pdf_folder'        :   User_Inputs.User_Value.pdf_folder,        
        'pdf_name'          :   User_Inputs.User_Value.pdf_name
        }

else: # Use the user interface
    config_user = start_gui()
    Inputs_dic = config_user


################################################################
# Loading Raw Data 
################################################################
# if Analysis_Type not in ['1D_Stack','Pseudo2D','1D']:
#     exit()

def analysis_Pseudo2D(imputs_dic):

    Analysis_Type = imputs_dic['Data_Type']

    ######################################################
    ##################### Read and Load Data #############
    ######################################################
    if Analysis_Type in ['Pseudo2D','1D']:
        [data_all, dic_all, x_ppm_all] = Read_Raw_NMR_Data_Bruker(
                path_nmr_data   =   os.path.join(imputs_dic['Data_Path'],imputs_dic['Data_Folder']),
                expno_data      =   imputs_dic['ExpNo'],
                procno_data     =   imputs_dic['ProcNo']
        )
    elif Analysis_Type in ['1D_Stack']:
        Raw_y_Data = []
        Raw_x_Data = []    
        Exp_List = [int(i) for i in imputs_dic['ExpNo'].split(',')]
        for n in Exp_List:
            [data, diC, x_ppm] = Read_Raw_NMR_Data_Bruker(
                    path_nmr_data   =   os.path.join(imputs_dic['Data_Path'],imputs_dic['Data_Folder']),
                    expno_data      =   n,
                    procno_data     =   imputs_dic['ProcNo']
            )       
            
            Raw_x_Data.append(x_ppm)  
            Raw_y_Data.append(data)  

        x_ppm_all = np.array(Raw_x_Data)
        data_all = np.array(Raw_y_Data)
    #-----------------------------------------------------#    

    ######################################################
    #Extract data within the region selected by the user##
    ######################################################
    [_Ext_data_, _Ext_x_ppm_] = Extract_Data(
        data     = data_all,
        x_ppm    = x_ppm_all,
        x_lim    = [imputs_dic['Spec_Lim'        ][0],imputs_dic['Spec_Lim'   ][1]]
    )
    #-----------------------------------------------------#   

    ######################################################
    ###########Extract the reference spectrum#############
    ######################################################
    if Analysis_Type == 'Pseudo2D':
        y_Spec_init_ = _Ext_data_[int(imputs_dic['Ref_Spec' ])-1,:]
        x_Spec_init_ = _Ext_x_ppm_
    elif Analysis_Type == '1D_Stack':
        y_Spec_init_ = _Ext_data_[int(imputs_dic['Ref_Spec' ])-1,:]
        x_Spec_init_ = _Ext_x_ppm_[int(imputs_dic['Ref_Spec' ])-1,:]
    elif Analysis_Type == '1D':
        y_Spec_init_ = _Ext_data_
        x_Spec_init_ = _Ext_x_ppm_
    #-----------------------------------------------------#   

    ######################################################
    ####################Peak Picking######################
    ######################################################
    Peak_Picking = Peak_Picking_1D(
    x_data          =   x_Spec_init_, 
    y_data          =   y_Spec_init_, 
    threshold       =   imputs_dic['Threshold'],
    )
    #-----------------------------------------------------#   

    ######################################################
    #############Manual Check of Peak Picking#############
    ######################################################
    new_th, pp_res_Sel = main_window(x_Spec_init_,y_Spec_init_,imputs_dic['Threshold'],Peak_Picking)
    check_for_nt = new_th.isnull().values.any()
    while check_for_nt == False:
        new_th = new_th.apply(pd.to_numeric, errors='coerce')
        pp_t = new_th.nt.values[0]

        Peak_Picking = Peak_Picking_1D(
            x_data          =   x_Spec_init_, 
            y_data          =   y_Spec_init_, 
            threshold       =   pp_t,
        )
        
        new_th, pp_res_Sel = main_window(x_Spec_init_,y_Spec_init_,pp_t,Peak_Picking)
        check_for_nt = new_th.isnull().values.any()
        if check_for_nt == True:
            break  
    cluster_list =  pp_res_Sel.Cluster.unique()
    #-----------------------------------------------------#   

    ######################################################
    #######################Fitting########################
    ######################################################
    if Analysis_Type in ['1D','1D_Stack','Pseudo2D']:
        Fit_results = Pseudo2D_PeakFitting(
                    Intensities  =   _Ext_data_,
                    x_Spec       =   x_Spec_init_,
                    ref_spec     =   imputs_dic['Ref_Spec'],
                    peak_picking_data = pp_res_Sel
            )

    #-----------------------------------------------------#   
    ######################################################
    #######################Output#########################
    ######################################################
    Plot_All_Spectrum(
        pdf_path = imputs_dic['pdf_path'],
        pdf_folder = imputs_dic['pdf_folder'],
        pdf_name = imputs_dic['pdf_name'],
        Fit_results= Fit_results,
        Int_Pseudo_2D_Data = _Ext_data_,
        x_ppm = x_Spec_init_,
        Peak_Picking_data= pp_res_Sel
    )
    print('Full Analysis is done')
    print('#--------#')  
    print('##########')
    return Peak_Picking


analysis_Pseudo2D(Inputs_dic)
exit()




