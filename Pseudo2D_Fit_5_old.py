import os, sys, importlib
from tkinter import * #required.
from tkinter import messagebox #for messagebox.
import tkinter.font as tkFont
import tkinter as tk
from scipy.optimize import curve_fit
from matplotlib.backends.backend_pdf import PdfPages
from c_py_mod.make_plot_grid import *
from scipy.optimize import minimize

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

import numpy as np
import nmrglue as ng
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tqdm import tqdm
from random import randint

class MyOptionMenu(tk.OptionMenu):
    def __init__(self, master, status, *options):
        self.var = tk.StringVar(master)
        self.var.set(status)
        tk.OptionMenu.__init__(self, master, self.var, *options)
        self.config(font=('calibri',(10)),bg='white',width=12)
        self['menu'].config(font=('calibri',(10)),bg='white')

# https://stackoverflow.com/questions/58367251/how-can-i-store-the-data-of-my-tkinter-entries-into-a-dataframe-to-later-export

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

def Read_Raw_NMR_Data_Bruker(
        path_nmr_data   =   'path_nmr_data',
        expno_data      =   'expno_data',
        procno_data     =   'procno_data',
        ):
    path = os.path.join(path_nmr_data,str(expno_data),'pdata',str(procno_data))
    dic, data = ng.bruker.read_pdata(
        path,
        read_procs=True,
        read_acqus=False,
        scale_data = False,
        all_components=False
        )
    n_dim = len(data.shape) 
    if n_dim == 1:       
        udic = ng.bruker.guess_udic(dic,data)
        uc_F1 = ng.fileiobase.uc_from_udic(udic, 0)
        ppm_scale_F1 = uc_F1.ppm_scale()
        output = [data,dic,ppm_scale_F1]
    if n_dim == 2:
        udic = ng.bruker.guess_udic(dic,data)
        uc_F2 = ng.fileiobase.uc_from_udic(udic, 1)
        ppm_scale_F2 = uc_F2.ppm_scale()
        # Clean data for data stopped before the end!
        data = data[~np.all(data == 0, axis=1)]

        output = (data,dic,ppm_scale_F2)
    return output

def Extract_Data(
    data = 'data',
    x_ppm = 'x_ppm',
    x_lim = 'x_lim'
    ):
    n_dim = len(data.shape) 
    if n_dim == 1:     
        idx_x0_F1, x0_F1 = find_nearest(x_ppm,x_lim[0])
        idx_x1_F1, x1_F1 = find_nearest(x_ppm,x_lim[1])
        data_ext = data[idx_x0_F1:idx_x1_F1]
        x_ppm_ext = x_ppm[idx_x0_F1:idx_x1_F1]
        output = [data_ext, x_ppm_ext]
    if n_dim == 2:

        idx_x0_F2, x0_F2 = find_nearest(x_ppm,x_lim[0])
        idx_x1_F2, x1_F2 = find_nearest(x_ppm,x_lim[1])
        data_ext = data[:,idx_x0_F2:idx_x1_F2]
        x_ppm_ext = x_ppm[idx_x0_F2:idx_x1_F2]
        output = [data_ext, x_ppm_ext]

    return output

def Peak_Picking_1D(
    x_data          =   'x_data', 
    y_data          =   'y_data', 
    threshold       =   'threshold',
    ):
    try: 
        peak_table = ng.peakpick.pick(
            y_data, 
            pthres=threshold, 
            algorithm='downward',
            )

        # Find peak locations in ppm
        peak_locations_ppm = []
        for i in range(len(peak_table['X_AXIS'])):
            pts = int(peak_table['X_AXIS'][i])
            peak_locations_ppm.append( x_data[pts])
        
        # Find the peak amplitudes
        peak_amplitudes = y_data[peak_table['X_AXIS'].astype('int')]

        results = pd.DataFrame(columns=['ppm_H_AXIS','Peak_Amp'],index=np.arange(1,len(peak_table)+1))
        results.loc[:,'ppm_H_AXIS'] = peak_locations_ppm
        results.loc[:,'Peak_Amp'] = peak_amplitudes

        results = results.sort_values(by='ppm_H_AXIS', ascending=True)
    except:
        main = Tk()
        main.title("Error")
        
        str_var = StringVar()
        #Message Function
        label = Message( main, textvariable=str_var, 
            relief=RAISED,width=400,foreground='red')
        def_font = tk.font.nametofont("TkDefaultFont")
        def_font.config(size=12)
        str_var.set("No signal were found \n Lower the threshold") 
        label.pack()
        main.mainloop()
        exit()

    return results

def Fit_Functions(
    Peak_Type   =   'Peak_Type',
    params      =   'Params'):

    if Peak_Type is Singlet: 
        [x, x0, a, h_s, lw] = params  
        f_fit = a * h_s  / ( 1 + (( x - x0 )/lw)**2) + (1-a)*h_s*np.exp(-(x-x0)**2/(2*lw**2)) 
    if Peak_Type is Doublet:
        [x, x0, a, h_s, lw, J1]  = params
        S1 = a * h_s  / ( 1 + (( x - x0 - (J1/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - (J1/2))**2/(2*lw**2))
        S2 = a * h_s  / ( 1 + (( x - x0 + (J1/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + (J1/2))**2/(2*lw**2))
        f_fit = S1 + S2 
    
def Singlet( x, x0, a, h_s, lw ):
    #Lorentzian + Gaussian    
    S1 = a * h_s  / ( 1 + (( x - x0 )/lw)**2) + (1-a)*h_s*np.exp(-(x-x0)**2/(2*lw**2))    
    Signal = S1
    return Signal

def Doublet( x, x0, a, h_s, lw, J1 ):
    #Lorentzian + Gaussian
    S1 = a * h_s  / ( 1 + (( x - x0 - (J1/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - (J1/2))**2/(2*lw**2))
    S2 = a * h_s  / ( 1 + (( x - x0 + (J1/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + (J1/2))**2/(2*lw**2))
    Signal = S1 + S2
    return Signal

def DoubletOfDoublet( x, x0, a, h_s, lw, J1, J2):
    #Lorentzian + Gaussian
    S1 = a * h_s  / ( 1 + (( x - x0 - ((J1+J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - ((J1+J2)/2))**2/(2*lw**2))
    S2 = a * h_s  / ( 1 + (( x - x0 - ((J1-J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - ((J1-J2)/2))**2/(2*lw**2))
    S3 = a * h_s  / ( 1 + (( x - x0 + ((J1+J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + ((J1+J2)/2))**2/(2*lw**2))
    S4 = a * h_s  / ( 1 + (( x - x0 + ((J1-J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + ((J1-J2)/2))**2/(2*lw**2))
    Signal = S1+S2+S3+S4
    return Signal

# x_p = np.arange(-400,400,0.1)
# y1 = DoubletOfDoublet(x_p, 0, 0.5, 1e4, 2, 20,100)
# y2 = Singlet(x_p, 0, 0.5, 1e5, 2)
# s = y1 + y2
# plt.plot(
#     x_p,
#     s
# )
# plt.show()
# exit()

d_mapping = {
    "Singlet":{"f_function":Singlet,"n_peaks" : 1, "params":['x0','a','Amp','lw']},
    "Doublet":{"f_function":Doublet,"n_peaks" : 2,"params":['x0','a','Amp','lw','J1']},
    "DoubletofDoublet":{"f_function":DoubletOfDoublet,"n_peaks" : 4,"params":['x0','a','Amp','lw','J1','J2']}

    }
d_clustering = {d_mapping[k]["n_peaks"]:k for k in d_mapping.keys()}

def Peak_Initialisation(
    Peak_Type='Peak_Type',
    Peak_Picking_Results = 'Peak_Picking_Results'):
    Peak_Picking_Results = Peak_Picking_Results.apply(pd.to_numeric)
    if Peak_Type == 'Singlet':
        Init_Val= [
        Peak_Picking_Results.ppm_H_AXIS.values[0], 
        0.5,
        Peak_Picking_Results.Peak_Amp.values[0], 
        0.002
        ]

    if Peak_Type =='Doublet':
        x0 = np.mean(Peak_Picking_Results.loc[:,'ppm_H_AXIS'])
        J1 = 2*(np.abs(Peak_Picking_Results.loc[2,'ppm_H_AXIS'])-np.abs(x0))
        Amp = np.mean(Peak_Picking_Results.loc[:,'Peak_Amp'])

        Init_Val= [
                x0, 
                0.5,
                Amp, 
                0.002,
                J1
                ]

    if Peak_Type =='DoubletofDoublet':

        x0_init = np.mean(Peak_Picking_Results.loc[:,'ppm_H_AXIS'])
        J_small = Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').diff(axis=0).ppm_H_AXIS.iloc[1]

        J_large = (np.mean(Peak_Picking_Results.nlargest(2, 'ppm_H_AXIS').ppm_H_AXIS)-np.mean(Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').ppm_H_AXIS))
        Amp_init = np.mean(Peak_Picking_Results.loc[:,'Peak_Amp'])
        Init_Val= [
                x0_init, 
                0.5,
                Amp_init, 
                0.002,
                J_small,
                J_large
                ]

    return Init_Val

def Peak_Fitting(
    Peak_Type   = 'Peak_Type',
    x_data      = 'x_data',
    y_data      = 'y_data',
    Peak_Picking_Results = 'Peak_Picking_Results',
    Initial_Values = 'Initial_Values'
    ):

    if Peak_Picking_Results is not None:
        Init_Val = Peak_Initialisation(Peak_Type,Peak_Picking_Results)

    if Initial_Values is None:
        Init = Init_Val
    else:
        Init = Initial_Values
    # print(isinstance(Peak_Type, str))

    popt,pcov = curve_fit(
        d_mapping[Peak_Type]["f_function"], 
        x_data, 
        y_data, 
        p0=Init
        )
    return popt,pcov

def Pseudo2D_PeakFitting(   
    Intensities =   'Intensities',
    x_Spec      =   'x_Spec',    
    ref_spec    =   'ref_spec',
    Peak_Type   =   'Peak_Type',
    Initial_Fitting = 'Initial_Fitting'
    ): 
    n_spec = Intensities.shape[0]
    ref_spec = int(ref_spec)-1
    spec_sup = np.arange(ref_spec+1,n_spec,1)
    spec_inf = np.arange(0,ref_spec,1)

    Col_Names = d_mapping[Peak_Type]["params"]
    Fit_results = pd.DataFrame(
        columns=Col_Names,
        index=np.arange(0,n_spec,1)
            )
    
    Fit_results.Spec = np.arange(1,n_spec+1,1)
    for n in range(len(Col_Names)-1):
        Fit_results.loc[ref_spec,str(Col_Names[n+1])] = Initial_Fitting[n]    

    for s in spec_sup:
        y_Spec = Intensities[s-1,:]
        Initial_Fit_Values = list(Fit_results.loc[s-1].iloc[1:].values)    
        try:
            popt, pcov = Peak_Fitting(
                Peak_Type = Peak_Type,
                x_data = x_Spec,
                y_data = y_Spec,
                Peak_Picking_Results = None,
                Initial_Values= Initial_Fit_Values
                )
            for n in range(len(Col_Names)-1):
                Fit_results.loc[s,str(Col_Names[n+1])] = popt[n]
        except:
            print('Error'+str(s))

    for s in spec_inf[::-1]:
        y_Spec = Intensities[s,:]   
        Initial_Fit_Values = list(Fit_results.loc[s+1].iloc[1:].values)    
        try:
            popt, pcov = Peak_Fitting(
                Peak_Type = Peak_Type,
                x_data = x_Spec,
                y_data = y_Spec,
                Peak_Picking_Results = None,
                Initial_Values= Initial_Fit_Values
                )
            for n in range(len(Col_Names)-1):
                Fit_results.loc[s,str(Col_Names[n+1])] = popt[n]
        except:
            print('Error'+str(s))

    return Fit_results

def Plot_All_Spectrum(
    pdf_path = 'pdf_path',
    pdf_name = 'pdf_name',
    Fit_results = 'Fit_results', 
    Int_Pseudo_2D_Data = 'Int_Pseudo_2D_Data',
    x_ppm = 'x_ppm',
    Peak_Type = 'Peak_Type' 
    ):

    n_col   = 4
    n_row   = 6
    n_spec_page = n_col*n_row
    n_spec = len(Fit_results)

    speclist = Fit_results.Spec
    with PdfPages(str(pdf_path)+str(pdf_name)+'.pdf') as pdf:
        for page in range(int(np.ceil(float(n_spec/n_spec_page)))):
            fig, ax = make_plot_grid(n_row, n_col)
            fig.set_size_inches([8.5,11])
            spec = sorted(list({int(i) for i in range(n_col*n_row*page,n_col*n_row*(page+1))}))
            
            spec_4_plot = np.arange(len(spec))
            for r in range(len(spec)):
                sp = spec[r]
                if sp in speclist:
                    ax[r].plot(
                        x_ppm,
                        Int_Pseudo_2D_Data[sp,:],
                        color='k',
                        ls='None',
                        marker='o',
                        markersize=0.5
                    )    
                    ax[r].invert_xaxis()
                    # ax[r].set_xlabel('PPM')
                    ax[r].set_ylim(bottom=-1e2)
                    res = Fit_results.loc[sp].iloc[1:]
                    ax[r].plot(
                        x_Spec, 
                        Peak_Type(x_Spec, *res), 
                        'r-', 
                        lw=0.6,
                        label='fit')

                    ax[r].text(0.05,0.9,sp+1,transform=ax[r].transAxes)  
                else:
                    ax[r].axis('off')

                if r not in spec_4_plot[-n_col:]:
                    ax[r].get_xaxis().set_ticklabels([])
                else: 
                    ax[r].set_xlabel(r'$^1H$ $(ppm)$')

                if r  in spec_4_plot[::n_col]:
                    ax[r].set_ylabel('Intensity')


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

def saveinfo(r,dic):
    Res.Peak_Amp = dic['Intensity']
    Res.ppm_H_AXIS = dic['Peak_Position']
    Res.Cluster = [i.get() for i in dic["Cluster"]]
    Res.Check = [i.get() for i in dic["Check"]]
    r.destroy()
    plt.close()

def save_nt(r, dic, new_threshold):
    for n in dic['th']:
        nt = n.get()
    new_threshold.nt.loc[1] = nt
    r.destroy()
    plt.close()
    return new_threshold

def Exit(r):
    r.destroy()
    plt.close()
    
def opennewwindow(PeakPicking_Threshold, pp_results,figure,pts_Color,Res,new_threshold):
    newwindow = tk.Tk()
    newwindow.title('Peak Picking Visualisation and Validation')
    graph = FigureCanvasTkAgg(figure, master=newwindow)
    canvas = graph.get_tk_widget()
    canvas.grid(row=0, column=0,columnspan = 8,rowspan=1)

    pp_names = ['ppm_H_AXIS','Peak_Amp']
    data_cols_names = ['1H ppm','Peak Intensity','Selection','Cluster']
    # Multiplicity_Choice = ('Singlet','Doublet')

    for c in range(len(data_cols_names)):
        tk.Label(newwindow, text=str(data_cols_names[c]), ).grid(column=c+1, row=2)

    dic = {
        'Cluster': [],
        'Check': [],
        'Intensity':[],
        'Peak_Position':[]
    }
    dic_par = {
        'th':[]
    }
    npeaks = len(pp_results)
    for i in range(npeaks):
        tk.Label(newwindow, text="Peak "+str(i+1),fg=pts_Color[i]).grid(column=0, row=i+3)
        en = tk.Entry(newwindow,justify = "center")

        # Button for peak selection
        check_resultat = tk.IntVar()
        dic['Check'].append(check_resultat)
        checkbutton1=Checkbutton(newwindow, var=check_resultat, onvalue=1,offvalue=0)
        checkbutton1.grid(row=i+3,column=len(data_cols_names)-1)

        # # Menu to choose mutliplicity
        # v = tk.StringVar()
        # v.set('Multiplicity')
        # dic['Multiplicity'].append(v)
        # OptionMenu1 = OptionMenu(newwindow, v, *Multiplicity_Choice)
        # OptionMenu1.grid(row=i+3,column=len(data_cols_names)-1)

        # Clustering
        en_cluster = tk.Entry(newwindow,justify = "center")
        en_cluster.insert(0, 0)
        dic['Cluster'].append(en_cluster)
        en_cluster.grid(column=len(data_cols_names),row=i+3,ipadx=5)

        for c in range(len(pp_names)):
            col = pp_names[c]
            en_c = tk.Entry(newwindow,justify = "center")
            data = pp_results.iloc[i].loc[col]
            if col == 'ppm_H_AXIS':
                dic['Peak_Position'].append(data)
            if col == 'Peak_Amp':
                dic['Intensity'].append(data)
            en_c.insert(0, round(data,3))
            en_c.grid(column=c+1,row=i+3,sticky=tk.N+tk.S+tk.E+tk.W)
    
    disp = Entry(newwindow, readonlybackground="white")
    tk.Label(newwindow, text="Threshold", fg='#f00').grid(column=0, row=1)
    disp.insert(0, PeakPicking_Threshold)
    disp.grid(column=1, row=1)
    dic_par['th'].append(disp)

    tk.Button(newwindow, text="Refresh & Close", fg = "orange", command=lambda: save_nt(newwindow, dic_par, new_threshold)).grid()  
    tk.Button(newwindow, text="Save & Close", fg = "blue", command=lambda: saveinfo(newwindow, dic)).grid() 
    tk.Button(newwindow, text="Exit", fg = "black", command=lambda: Exit(newwindow)).grid() 

    newwindow.mainloop()

Res = pd.DataFrame(columns=['ppm_H_AXIS','Peak_Amp','Check','Cluster'])

def main_window(x_Spec,y_Spec,PeakPicking_Threshold,PeakPicking_data):

    n_peak = len(PeakPicking_data)
    if n_peak >=10:
        PeakPicking_data = PeakPicking_data.sort_values(by='Peak_Amp', ascending=False).head(10)
        PeakPicking_data = PeakPicking_data.sort_values(by='ppm_H_AXIS', ascending=True)
        n_peak = len(PeakPicking_data)

    #Res = pd.DataFrame(columns=['ppm_H_AXIS','Peak_Amp','Check','Cluster'],index=np.arange(1,n_peak+1))
    new_threshold = pd.DataFrame(columns=['nt'],index=[1])

    # Create a list of colors
    colors = []
    for i in range(n_peak):
        colors.append('#%06X' % randint(0, 0xFFFFFF))

    #Plot Spectrum with peak picking
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(x_Spec, y_Spec, '-',color='teal')
    for i in range(n_peak):
        ax.plot(PeakPicking_data.ppm_H_AXIS.iloc[i],PeakPicking_data.Peak_Amp.iloc[i],c=colors[i],ls='none',marker='o')
    ax.axhline(PeakPicking_Threshold,c='r')
    ax.invert_xaxis()
    ax.set_xlabel(r'$^1H$ $(ppm)$')

    opennewwindow(
        PeakPicking_Threshold,
        PeakPicking_data, 
        fig,
        colors,
        Res,
        new_threshold
        )

    return new_threshold, Res


## Test for singlet
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/home-local/charlier/nmrData/Neil', '8NC2021_ColiCE-NAD', '204', '1','36', '8.4', '8.2', '0.1e4']
### Test for Doublet
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/home-local/charlier/nmrData/Neil', '8NC2021_ColiCE-NAD', 'Pseudo2D','204', '1','36', '0.15', '-0.15', '0.1e4']

# ## Test for singlet
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/home-local/charlier/nmrData/Neil', '8NC2021_ColiCE-Glc1-2-13C', '6', '1','17', '8.48', '8.470', '0.1e4']

# ################### Test Pierre Data
test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/opt/topspin4.0.8/data/', '210618', '1D','52', '1','1', '2.1', '1.7', '0.1e4']

################### Test Plastic
# test = ['/opt/topspin4.0.8/exp/stan/nmr/py/user/Pseudo2D_Fit.py', '/opt/topspin4.0.8/data/', '9CC_900', '1D_Stack',['504','511], '1','1', '8.5', '7.5', '0.1e4']
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

PeakPicking_Threshold = 3e5

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
x_Spec_init_ = _Ext_x_ppm_
################################################################
# Initial 1D Peak Picking 
################################################################
Peak_Picking = Peak_Picking_1D(
    x_data          =   x_Spec_init_, 
    y_data          =   y_Spec_init_, 
    threshold       =   PeakPicking_Threshold,
)
# ################################################################
# # Manual Check of Peak Picking
# ################################################################
# new_th, pp_res_Sel = main_window(x_Spec_init_,y_Spec_init_,PeakPicking_Threshold,Peak_Picking)
# ################################################################
# # Manual Check of Peak Picking 7 new Peak picking if user asks for it
# ################################################################
# check_for_nt = new_th.isnull().values.any()
# while check_for_nt == False:
#     new_th = new_th.apply(pd.to_numeric, errors='coerce')
#     pp_t = new_th.nt.values[0]

#     Peak_Picking = Peak_Picking_1D(
#         x_data          =   x_Spec_init_, 
#         y_data          =   y_Spec_init_, 
#         threshold       =   pp_t,
#     )
    
#     new_th, pp_res_Sel = main_window(x_Spec_init_,y_Spec_init_,pp_t,Peak_Picking)
#     check_for_nt = new_th.isnull().values.any()
#     if check_for_nt == True:
#         break   


################################################################
# Initial 1D Peak Fitting 
################################################################
# print(Res)
# exit()
Peak_Picking['Cluster'] = [0,0,1,0,0]
pp_res_Sel = Peak_Picking
cluster_list =  pp_res_Sel.Cluster.unique()
d_id = {k:[] for k in cluster_list}
print(d_id)
ini_params = []

for n in cluster_list:
    _cluster_ = pp_res_Sel.loc[pp_res_Sel.Cluster==n]
    _multiplet_type_ = d_clustering[len(_cluster_)]
    _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
    Init_Val = Peak_Initialisation(_multiplet_type_,Peak_Picking_Results=_cluster_)

    d_id[n] = [len(ini_params),len(ini_params)+len(Init_Val)]
    ini_params.extend(Init_Val)

def simulate_data(
    x_fit_,
    peakpicking_data,
    fit_par, 
    ):
    sim_intensity = np.zeros(len(x_fit_))
    cluster_list =  peakpicking_data.Cluster.unique()
    print(d_id)
    # print(fit_par)
    for n in cluster_list:
        _cluster_ = peakpicking_data.loc[peakpicking_data.Cluster==n]
        _multiplet_type_ = d_clustering[len(_cluster_)]
        _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
        params = fit_par[d_id[n][0]:d_id[n][1]] 
        y = _multiplet_type_function(x_fit_, *params)
        sim_intensity += y
    return sim_intensity  

def fit_objective(
    fit_par,
    x_fit_,
    peakpicking_data,
    y_Spec,
    ):
    sim_intensity = simulate_data(x_fit_,peakpicking_data,fit_par)
    rmsd = np.sqrt(np.mean((sim_intensity - y_Spec)**2))
    return rmsd

res_fit = minimize(
    fit_objective,
    x0=ini_params,
    bounds=[
        (0,np.inf),
        (0,np.inf),
        (0,np.inf),
        (0,np.inf),
        (0,np.inf),
        (0,np.inf),
        (0,np.inf),
        (0,np.inf),
        (0,np.inf),
        (0,np.inf),
    ],
    method='SLSQP',
    options={'ftol': 1e-6},#,'maxiter':0},
    args=(x_Spec_init_,pp_res_Sel,y_Spec_init_),
    )

# rmsd = fit_objective(
#     x_Spec_init_,
#     pp_res_Sel,
#     y_Spec_init_,
#     ini_params
#     )

sim = simulate_data(
    x_Spec_init_,
    pp_res_Sel,
    res_fit.x.tolist()
)
print(res_fit.x.tolist())
plt.plot(x_Spec_init_,y_Spec_init_,'o')
plt.plot(x_Spec_init_,sim)
plt.show()

exit()
# for n in range(pp_res_Sel.Cluster.value.unique())

Peak_Type_0_ = d_clustering[len(Cluster_0_)]

popt_init, pcov_init = Peak_Fitting(
    Peak_Type = Peak_Type_0_,
    x_data = x_Spec,
    y_data = y_Spec,
    Peak_Picking_Results = pp_res_Sel,
    Initial_Values = None
)

################################################################
# Initial 1D Peak Picking Visualisation 
################################################################
#plot the spectrum and peak locations on a PPM scale
plt.close()
fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(x_Spec, y_Spec, 'k-')
ax.plot(Peak_Picking.ppm_H_AXIS,Peak_Picking.Peak_Amp, 'ro')
ax.plot(x_Spec, d_mapping[Peak_Type_0_]["f_function"](x_Spec, *popt_init), 'r-', label='fit')
ax.invert_xaxis()
ax.set_xlabel(r'$^1H$ $(ppm)$')
plt.show()

################################################################
# Fit of Pseudo 2D 
################################################################
Fit_results = Pseudo2D_PeakFitting(
   Intensities  =   Int_Pseudo2D_Spec,
   x_Spec       =   x_Spec,
   ref_spec     =   topspin_dic['1D_ProcNo'],
   Peak_Type    =   d_mapping[Peak_Type_0_]["f_function"],
   Initial_Fitting = popt_init
)

################################################################
# Plot of the fit 
################################################################
Plot_All_Spectrum(
    pdf_path = '/home_pers/charlier/Bureau/',
    pdf_name = 'test0',
    Fit_results= Fit_results,
    Int_Pseudo_2D_Data = Int_Pseudo2D_Spec,
    x_ppm = x_Spec,
    Peak_Type= d_mapping[Peak_Type_0_]["f_function"]
)

plt.plot(Fit_results.loc[:,'Amp'])
plt.show()
