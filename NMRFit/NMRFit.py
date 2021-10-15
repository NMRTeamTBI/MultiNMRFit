from Multiplets import *
from Interfaces import *
from Utils_nmrData import *
from Fitting import *

import sys
################################################################
# Test for missing librairies 
################################################################
# if sys.argv[1] == "test":
#     libfn = os.path.normpath(os.path.join(sys.argv[2],"vd_hsqc_lib.txt"))
#     txt = ""
#     modules = ["numpy","matplotlib","nmrglue","pandas","tkinter","tqdm"]
#     for modname in modules:
#         try:
#             globals()[modname] = importlib.import_module(modname)
#             txt += "\nLibrary installed : "+str(modname) 
#         except ImportError as e:
#             main = Tk()
#             main.title("Error")
#             str_var = StringVar()
#             def_font = tk.font.nametofont("TkDefaultFont")
#             def_font.config(size=16)
#             #Message Function
#             label = Message( main, textvariable=str_var, 
#                 relief=RAISED,width=200)
#             str_var.set(str(modname)+" is missing") 
#             label.pack()
#             main.mainloop()
#             txt += "\nLibrary missing : "+str(modname) 
#     libf = open(libfn, 'w')
#     libf.write(txt)
#     libf.close()
#     exit()
################################################################

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

Analysis_Type = Inputs_dic['Data_Type']

################################################################
# Loading Raw Data 
################################################################
if Analysis_Type not in ['1D_Stack','Pseudo2D','1D']:
    exit()

if Analysis_Type == '1D_Stack':
    Raw_y_Data = []
    Raw_x_Data = []    
    Exp_List = [int(i) for i in Inputs_dic['ExpNo'].split(',')]
    for n in Exp_List:
        [data_1D, dic_1D, x_ppm_1D] = Read_Raw_NMR_Data_Bruker(
                path_nmr_data   =   os.path.join(Inputs_dic['Data_Path'],Inputs_dic['Data_Folder']),
                expno_data      =   n,
                procno_data     =   Inputs_dic['ProcNo']
        )       
        
        Raw_x_Data.append(x_ppm_1D)  
        Raw_y_Data.append(data_1D)  

    _dic_ = dic_1D
    _x_ppm_ = np.array(Raw_x_Data)
    _data_ = np.array(Raw_y_Data)

elif Analysis_Type == 'Pseudo2D':
    [data_2D, dic_2D, x_ppm_2D] = Read_Raw_NMR_Data_Bruker(
            path_nmr_data   =   os.path.join(Inputs_dic['Data_Path'],Inputs_dic['Data_Folder']),
            expno_data      =   Inputs_dic['ExpNo'],
            procno_data     =   Inputs_dic['ProcNo']
    )

    _dic_ = dic_2D
    _x_ppm_ = x_ppm_2D
    _data_ = data_2D

elif Analysis_Type == '1D':
    [data_1D, dic_1D, x_ppm_1D] = Read_Raw_NMR_Data_Bruker(
            path_nmr_data   =   os.path.join(Inputs_dic['Data_Path'],Inputs_dic['Data_Folder']),
            expno_data      =   Inputs_dic['ExpNo'],
            procno_data     =   Inputs_dic['ProcNo']
    )
    _dic_ = dic_1D
    _x_ppm_ = x_ppm_1D
    _data_ = data_1D

################################################################
# Extract 2D Data in the region of interest 
################################################################
[_Ext_data_, _Ext_x_ppm_] = Extract_Data(
    data     = _data_,
    x_ppm    = _x_ppm_,
    x_lim    = [Inputs_dic['Spec_Lim'        ][0],Inputs_dic['Spec_Lim'   ][1]]
)

# ################################################################
# # Extract 1D Data for intitial fitting 
# ################################################################
if Inputs_dic['Data_Type'] == 'Pseudo2D':
    y_Spec_init_ = _Ext_data_[int(Inputs_dic['Ref_Spec' ])-1,:]
    x_Spec_init_ = _Ext_x_ppm_
if Inputs_dic['Data_Type'] == '1D_Stack':
    y_Spec_init_ = _Ext_data_[int(Inputs_dic['Ref_Spec' ])-1,:]
    x_Spec_init_ = _Ext_x_ppm_[int(Inputs_dic['Ref_Spec' ])-1,:]
if Inputs_dic['Data_Type'] == '1D':
    y_Spec_init_ = _Ext_data_
    x_Spec_init_ = _Ext_x_ppm_

################################################################
# Initial 1D Peak Picking 
################################################################
Peak_Picking = Peak_Picking_1D(
    x_data          =   x_Spec_init_, 
    y_data          =   y_Spec_init_, 
    threshold       =   Inputs_dic['Threshold'],
)
# ################################################################
# # Manual Check of Peak Picking
# ################################################################
new_th, pp_res_Sel = main_window(x_Spec_init_,y_Spec_init_,Inputs_dic['Threshold'],Peak_Picking)
# ################################################################
# # Manual Check of Peak Picking 7 new Peak picking if user asks for it
# ################################################################
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

################################################################
# Initial 1D Peak Fitting 
################################################################

if Inputs_dic['Data_Type'] == '1D':
    _1D_Fit_ = Fitting_Function(
            x_Spec_init_,
            pp_res_Sel,
            y_Spec_init_)
    d_id = Initial_Values(pp_res_Sel, x_Spec_init_)[0]
    sim = simulate_data(
            x_Spec_init_,
            pp_res_Sel,
            _1D_Fit_.x.tolist(),
            d_id)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_Spec_init_,y_Spec_init_,'o')
    ax.plot(x_Spec_init_,sim, 'r-', label='fit')

    ax.invert_xaxis()
    ax.set_xlabel(r'$^1H$ $(ppm)$')
    plt.show()
    plt.close()
    exit()

if Inputs_dic['Data_Type'] in ['1D_Stack','Pseudo2D']:
    Fit_results = Pseudo2D_PeakFitting(
                Intensities  =   _Ext_data_,
                x_Spec       =   x_Spec_init_,
                ref_spec     =   Inputs_dic['Ref_Spec'],
                peak_picking_data = pp_res_Sel
               # scaling = Inputs_dic['Scaling']
        )
# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#     print(Fit_results)
################################################################
# Plot of the fit 
################################################################
Plot_All_Spectrum(
    pdf_path = Inputs_dic['pdf_path'],
    pdf_folder = Inputs_dic['pdf_folder'],
    pdf_name = Inputs_dic['pdf_name'],
    Fit_results= Fit_results,
    Int_Pseudo_2D_Data = _Ext_data_,
    x_ppm = x_Spec_init_,
    Peak_Picking_data= pp_res_Sel
    #scaling = Inputs_dic['Scaling']
    #Peak_Type= d_mapping[Peak_Type_0_]["f_function"]
)

print('Full Analysis is done')
print('#--------#')  
print('##########')
