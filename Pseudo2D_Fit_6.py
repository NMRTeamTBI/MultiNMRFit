from matplotlib.backends.backend_pdf import PdfPages


from Multiplets import *
from Interfaces import *
from Utils_nmrData import *
from Fitting import *
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

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from tqdm import tqdm

# https://stackoverflow.com/questions/58367251/how-can-i-store-the-data-of-my-tkinter-entries-into-a-dataframe-to-later-export

def Plot_All_Spectrum(
    pdf_path = 'pdf_path',
    pdf_name = 'pdf_name',
    Fit_results = 'Fit_results', 
    Int_Pseudo_2D_Data = 'Int_Pseudo_2D_Data',
    x_ppm = 'x_ppm',
    Peak_Picking_data = 'Peak_Picking_data'
    ):

    Fit_results.to_csv(str(pdf_path)+str(pdf_name)+'.txt', index=True)  

    x_fit = np.linspace(np.min(x_ppm),np.max(x_ppm),2048)
    speclist = Fit_results.index.values.tolist() 
    with PdfPages(str(pdf_path)+str(pdf_name)+'.pdf') as pdf:           
        for r in speclist:
            fig, (ax) = plt.subplots(1, 1)
            fig.set_size_inches([11.7,8.3])
            Norm = np.max(Int_Pseudo_2D_Data[r,:])
            ax.plot(
                x_ppm,
                Int_Pseudo_2D_Data[r,:],#/Norm,
                color='b',
                ls='None',
                marker='o',
                markersize=0.5
                )    
            ax.invert_xaxis()
            # ax[r].set_xlabel('PPM')
            #ax.set_ylim(top=1.1,bottom=-0.1)
            res = Fit_results.loc[r].iloc[:].values.tolist()

            sim = simulate_data(
                x_fit,
                Peak_Picking_data,
                res
                )

            ax.plot(
                x_fit, 
                sim,#/Norm, 
                'r-', 
                lw=0.6,
                label='fit')
            ax.text(0.05,0.9,r+1,transform=ax.transAxes)  
 
            ax.set_ylabel('Intensity')
            ax.set_xlabel(r'$^1H$ $(ppm)$')


            plt.subplots_adjust(
                left = 0.1,
                #bottom = 0.04,
                right = 0.96,
                top = 0.96,
                wspace = 0.3,
                hspace = 0.3,
            )
            pdf.savefig(fig)
            plt.close(fig)


## Test for singlet
test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/opt/topspin4.0.8/data/', '8NC2021_ColiCE-NAD', 'Pseudo2D', '204', '1','48', '8.35', '8.3', '0.1e4']
### Test for Doublet
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/opt/topspin4.0.8/data/', '8NC2021_ColiCE-NAD', 'Pseudo2D','204', '1','36', '0.15', '-0.15', '0.1e4']

# ## Test for singlet
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/home-local/charlier/nmrData/Neil', '8NC2021_ColiCE-Glc1-2-13C', '6', '1','17', '8.48', '8.470', '0.1e4']

# ################### Test Pierre Data
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/opt/topspin4.0.8/data/', '210618', '1D','52', '1','1', '2.1', '1.7', '0.1e4']

################### Test Plastic
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/opt/topspin4.0.8/data/', '9CC_900', '1D_Stack',['504','511'], '1','1', '8.5', '7.5', '0.1e4']
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/opt/topspin4.0.8/data/', '9CC_900', '1D','511', '1','1', '8.5', '7.5', '20e6']

topspin_dic = {
    'Path': str(test[1]),
    'Data_Folder': test[2], 
    'Data_Type': test[3],
    'Pseudo2D_ExpNo': int(test[4]) if len(test[4]) == 1 else test[4], 
    '2D_ProcNo': test[5], 
    '1D_ProcNo': test[6], 
    'Selected_window':[float(test[7]),float(test[8])]    
    }

PeakPicking_Threshold = 8e6

Analysis_Type = topspin_dic['Data_Type']

# topspin_dic = {
#     'Path': str(sys.argv[1]),
#     'Data_Folder': sys.argv[2], 
#     'Pseudo2D_ExpNo': int(sys.argv[3]), 
#     '1D_ProcNo': sys.argv[4], 
#     'Selected_window':[float(sys.argv[5]),float(sys.argv[6])]    
#     }

################################################################
# Loading Raw Data 
################################################################
if Analysis_Type is '1D_Stack':
    Raw_Data = []
    for n in topspin_dic['Pseudo2D_ExpNo']:
        [data_1D, dic_1D, x_ppm_1D] = Read_Raw_NMR_Data_Bruker(
                path_nmr_data   =   os.path.join(topspin_dic['Path'],topspin_dic['Data_Folder']),
                expno_data      =   int(n),
                procno_data     =   topspin_dic['2D_ProcNo']
        )       
        Raw_Data.append(data_1D)  

    _dic_ = dic_1D
    _x_ppm_ = x_ppm_1D
    _data_ = np.array(Raw_Data)

if Analysis_Type is 'Pseudo2D':
    [data_2D, dic_2D, x_ppm_2D] = Read_Raw_NMR_Data_Bruker(
            path_nmr_data   =   os.path.join(topspin_dic['Path'],topspin_dic['Data_Folder']),
            expno_data      =   topspin_dic['Pseudo2D_ExpNo'],
            procno_data     =   topspin_dic['2D_ProcNo']
    )
    _dic_ = dic_2D
    _x_ppm_ = x_ppm_2D
    _data_ = data_2D

if Analysis_Type is '1D':
    [data_1D, dic_1D, x_ppm_1D] = Read_Raw_NMR_Data_Bruker(
            path_nmr_data   =   os.path.join(topspin_dic['Path'],topspin_dic['Data_Folder']),
            expno_data      =   topspin_dic['Pseudo2D_ExpNo'],
            procno_data     =   topspin_dic['2D_ProcNo']
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
    x_lim    = [topspin_dic['Selected_window'][0],topspin_dic['Selected_window'][1]]
)

# ################################################################
# # Extract 1D Data for intitial fitting 
# ################################################################
if topspin_dic['Data_Type'] == 'Pseudo2D':
    y_Spec_init_ = _Ext_data_[int(topspin_dic['1D_ProcNo'])-1,:]
if topspin_dic['Data_Type'] == '1D_Stack':
    y_Spec_init_ = _Ext_data_[1,:]
if topspin_dic['Data_Type'] == '1D':
    y_Spec_init_ = _Ext_data_
################################################################
# Initial 1D Peak Picking 
################################################################
Peak_Picking = Peak_Picking_1D(
    x_data          =   _Ext_x_ppm_, 
    y_data          =   y_Spec_init_, 
    threshold       =   PeakPicking_Threshold,
)
# ################################################################
# # Manual Check of Peak Picking
# ################################################################
new_th, pp_res_Sel = main_window(_Ext_x_ppm_,y_Spec_init_,PeakPicking_Threshold,Peak_Picking)
# ################################################################
# # Manual Check of Peak Picking 7 new Peak picking if user asks for it
# ################################################################
check_for_nt = new_th.isnull().values.any()
while check_for_nt == False:
    new_th = new_th.apply(pd.to_numeric, errors='coerce')
    pp_t = new_th.nt.values[0]

    Peak_Picking = Peak_Picking_1D(
        x_data          =   _Ext_x_ppm_, 
        y_data          =   y_Spec_init_, 
        threshold       =   pp_t,
    )
    
    new_th, pp_res_Sel = main_window(_Ext_x_ppm_,y_Spec_init_,pp_t,Peak_Picking)
    check_for_nt = new_th.isnull().values.any()
    if check_for_nt == True:
        break  
cluster_list =  pp_res_Sel.Cluster.unique()
################################################################
# Initial 1D Peak Fitting 
################################################################

if topspin_dic['Data_Type'] == '1D':
    _1D_Fit_ = Fitting_Function(
            _Ext_x_ppm_,
            pp_res_Sel,
            y_Spec_init_)
    
    sim = simulate_data(
            _Ext_x_ppm_,
            pp_res_Sel,
            _1D_Fit_.x.tolist())


    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(_Ext_x_ppm_,y_Spec_init_,'o')
    ax.plot(_Ext_x_ppm_,sim, 'r-', label='fit')
    ax.invert_xaxis()
    ax.set_xlabel(r'$^1H$ $(ppm)$')
    plt.show()
    plt.close()
    exit()

if topspin_dic['Data_Type'] == 'Pseudo2D':
    Fit_results = Pseudo2D_PeakFitting(
                Intensities  =   _Ext_data_,
                x_Spec       =   _Ext_x_ppm_,
                ref_spec     =   topspin_dic['1D_ProcNo'],
                peak_picking_data = pp_res_Sel
        )
# with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
#     print(Fit_results)
################################################################
# Plot of the fit 
################################################################
Plot_All_Spectrum(
    pdf_path = './',
    pdf_name = 'test0',
    Fit_results= Fit_results,
    Int_Pseudo_2D_Data = _Ext_data_,
    x_ppm = _Ext_x_ppm_,
    Peak_Picking_data= pp_res_Sel
    #Peak_Type= d_mapping[Peak_Type_0_]["f_function"]
)

