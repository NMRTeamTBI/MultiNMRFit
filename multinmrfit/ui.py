from json.decoder import JSONDecodeError
from tkinter import * 
from tkinter import simpledialog
from tkinter import filedialog
import tkinter.font as tkFont
import tkinter as tk
from PIL import Image, ImageTk
from tkinter import ttk
from tkinter import filedialog as fd
from datetime import date
import pandas as pd
from random import randint
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib
matplotlib.use("TkAgg")
import numpy as np
import os 
import multinmrfit.run as nmrr
import multinmrfit.multiplets as nmrm
import multinmrfit.fitting as nmrf
import pkg_resources
import json

class MyOptionMenu(tk.OptionMenu):
    def __init__(self, master, status, *options):
        self.var = tk.StringVar(master)
        self.var.set(status)
        tk.OptionMenu.__init__(self, master, self.var, *options)
        self.config(font=('calibri',(10)),bg='white',width=12)
        self['menu'].config(font=('calibri',(10)),bg='white')
###################################
# Peak Picking window
###################################

def save_info_clustering(r,dic, Res):
    Res.Peak_Amp = dic['Intensity']
    Res.ppm_H_AXIS = dic['Peak_Position']
    Res.Options = [i.get() for i in dic["Options"]]
    Res.Cluster = [i.get() for i in dic["Cluster"]]
    Res.Selection = [True if i.get() != '' else False for i in dic["Cluster"]]
    r.destroy()
    plt.close()

def refresh_threshold(r, dic, new_threshold):
    for n in dic['th']:
        nt = n.get()
    new_threshold.nt.loc[1] = nt
    r.destroy()
    plt.close()
    return new_threshold

def Exit(r):
    r.destroy()
    plt.close()
    exit()

def wdw_peak_picking(PeakPicking_Threshold, pp_results,figure,pts_Color,Res,new_threshold):
    wdw = tk.Tk()
    wdw.title('Peak Picking Visualisation and Validation')
    graph = FigureCanvasTkAgg(figure, master=wdw)
    canvas = graph.get_tk_widget()
    canvas.grid(row=0, column=0,columnspan = 8,rowspan=1)

    pp_names = ['ppm_H_AXIS','Peak_Amp']
    data_cols_names = ['1H ppm','Peak Intensity','Cluster','Options']
    # Multiplicity_Choice = ('Singlet','Doublet')
    
    for c in range(len(data_cols_names)):
        tk.Label(wdw, text=str(data_cols_names[c]), ).grid(column=c+1, row=2)

    dic = {
        'Cluster': [],
        'Selection': [],
        'Intensity':[],
        'Peak_Position':[],
        'Options':[]
    }
    dic_par = {
        'th':[]
    }
    npeaks = len(pp_results)
    for i in range(npeaks):
        tk.Label(wdw, text="Peak "+str(i+1),fg=pts_Color[i]).grid(column=0, row=i+3)
        en = tk.Entry(wdw,justify = "center")
       
        # Clustering
        en_cluster = tk.Entry(wdw,justify = "center")
        en_cluster.insert(0, '')
        dic['Cluster'].append(en_cluster)
        en_cluster.grid(column=len(data_cols_names)-1,row=i+3,ipadx=5)
        
        listofoptions=['Roof'] # options
        en_options = ttk.Combobox(wdw, values=listofoptions) # Combobox
        en_options.grid(row=i+3,column=len(data_cols_names),ipadx=6) # adding to grid
        dic['Options'].append(en_options)

        for c in range(len(pp_names)):
            col = pp_names[c]
            en_c = tk.Entry(wdw,justify = "center")
            data = pp_results.iloc[i].loc[col]
            if col == 'ppm_H_AXIS':
                dic['Peak_Position'].append(data)
            if col == 'Peak_Amp':
                dic['Intensity'].append(data)
            en_c.insert(0, round(data,3))
            en_c.grid(column=c+1,row=i+3,sticky=tk.N+tk.S+tk.E+tk.W)
    
    disp = Entry(wdw, readonlybackground="white")
    tk.Label(wdw, text="Threshold", fg='#f00').grid(column=0, row=1)
    disp.insert(0, PeakPicking_Threshold)
    disp.grid(column=1, row=1)
    dic_par['th'].append(disp)

    tk.Button(wdw, text="Refresh & Close", fg = "orange", command=lambda: refresh_threshold(wdw, dic_par, new_threshold)).grid()  
    tk.Button(wdw, text="Save & Close", fg = "blue", command=lambda: save_info_clustering(wdw, dic, Res)).grid() 
    tk.Button(wdw, text="Exit", fg = "black", command=lambda: Exit(wdw)).grid() 

    wdw.mainloop()

def initialize_results_clustering():
    Res = pd.DataFrame(columns=['ppm_H_AXIS','Peak_Amp','Selection','Cluster','Options'])
    return Res

def filter_multiple_clusters(Res):
    for i,j in enumerate(Res.Cluster):
        cluster_num = j.split(',')
        if len(cluster_num) > 1:
            for k in cluster_num:
                new_pk = {'ppm_H_AXIS': Res.iloc[i].ppm_H_AXIS,'Peak_Amp': Res.iloc[i].Peak_Amp,'Selection': Res.iloc[i].Selection,'Cluster': k}
                Res = Res.append(new_pk, ignore_index = True)
            Res = Res.drop(Res.index[i])
    print(Res)
    return Res

def gui_peak_picking(x_Spec,y_Spec,PeakPicking_Threshold,PeakPicking_data):

    n_peak = len(PeakPicking_data)
    if n_peak >=10:
        PeakPicking_data = PeakPicking_data.sort_values(by='Peak_Amp', ascending=False).head(10)
        PeakPicking_data = PeakPicking_data.sort_values(by='ppm_H_AXIS', ascending=True)
        n_peak = len(PeakPicking_data)

    #Res = pd.DataFrame(columns=['ppm_H_AXIS','Peak_Amp','Check','Cluster'],index=np.arange(1,n_peak+1))
    Res = initialize_results_clustering()
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

    wdw_peak_picking(
        PeakPicking_Threshold,
        PeakPicking_data, 
        fig,
        colors,
        Res,
        new_threshold
        )
    Res = filter_multiple_clusters(Res)
    return new_threshold, Res

###################################
# Final Plots
###################################

def getList(dict):
    return [k for k in dict.keys()]

def getIntegral(x_fit_, _multiplet_type_, fit_par):
    d_mapping = nmrm.mapping_multiplets()[0]
    _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
    y = _multiplet_type_function(x_fit_, *fit_par)
    integral = np.sum(y)*(x_fit_[1]-x_fit_[0])
    return integral

def Plot_All_Spectrum(
    pdf_path = 'pdf_path',
    pdf_folder = 'pdf_folder',
    pdf_name = 'pdf_name',
    Fit_results = 'Fit_results', 
    Int_Pseudo_2D_Data = 'Int_Pseudo_2D_Data',
    x_ppm = 'x_ppm',
    Peak_Picking_data = None,
    scaling_factor=None,
    gui=False,
    id_spectra=None
    ):

    print('Plot in pdf file')  
    x_fit = np.linspace(np.min(x_ppm),np.max(x_ppm),2048)
    d_id = nmrf.Initial_Values(Peak_Picking_data, x_fit, scaling_factor)[0]
    #d_id = {k:[] for k in Peak_Picking_data.Cluster.unique()}
    cluster_list = getList(d_id)
    if id_spectra is None:
        id_spectra = np.arange(1,len(Fit_results)+1)
    Fit_results = Fit_results.apply(pd.to_numeric)
    Fit_results_text= Fit_results.round(9)
    
    if not os.path.exists(os.path.join(pdf_path,pdf_folder)):
        os.makedirs(os.path.join(pdf_path,pdf_folder))
    d_mapping, _, d_parameters = nmrm.mapping_multiplets()
    for i in cluster_list:        
        col = range(d_id[i][1][0],d_id[i][1][1])
        _multiplet_type_ = d_parameters[len(col)]
        _multiplet_params_ = d_mapping[_multiplet_type_]['params']
        mutliplet_results = Fit_results_text[Fit_results_text.columns.intersection(col)]
        mutliplet_results.columns = _multiplet_params_
        mutliplet_results["integral"] = [scaling_factor*getIntegral(x_fit, _multiplet_type_, row.tolist()) for index, row in mutliplet_results.iterrows()]
        mutliplet_results["Amp"] = scaling_factor*mutliplet_results["Amp"]
        mutliplet_results['exp_no'] = id_spectra
        mutliplet_results.set_index('exp_no', inplace=True)
        mutliplet_results.to_csv(
            os.path.join(pdf_path,pdf_folder,pdf_name+'_'+str(_multiplet_type_)+'_'+str(i)+'.txt'), 
            index=True, 
            sep = '\t'
            )
        
    speclist = Fit_results.index.values.tolist()
    
    if gui:
        from tqdm.gui import tqdm
        leave=False
    else:
        from tqdm import tqdm
        leave=True
    
    with PdfPages(os.path.join(pdf_path,pdf_folder,pdf_name+'.pdf')) as pdf:           
        for r in tqdm(speclist, leave=leave):
            fig, (ax) = plt.subplots(1, 1)
            fig.set_size_inches([11.7,8.3])
            ax.plot(
                x_ppm,
                Int_Pseudo_2D_Data[r,:],
                color='b',
                ls='None',
                marker='o',
                markersize=0.5
                )    
            ax.invert_xaxis()
            # ax[r].set_xlabel('PPM')
            #ax.set_ylim(top=1.1,bottom=-0.1)
            res = Fit_results.loc[r].iloc[:].values.tolist()

            sim = nmrf.simulate_data(
                x_fit,
                res,
                d_id,
                scaling_factor
                )

            ax.plot(
                x_fit, 
                sim,#/Norm, 
                'r-', 
                lw=0.6,
                label='fit')
            ax.text(0.05,0.9,"Spectra : " +str(id_spectra[r]),transform=ax.transAxes,fontsize=20)  
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
    print('#--------#')

###################################
# Error interface
###################################

def error_interface(message):
    gui_int = tk.Tk()
    gui_int.title("Error")
    gui_int.configure(bg='#FFFFFF')

    label = Label(gui_int, text=message,font=("Helvetica",18),bg='#FFFFFF',borderwidth=20)
    label.pack()

    close_button = Button(
        gui_int,
        text="Close ",
        # fg='#FFFFFF',
        font=("Helvetica", 14),
        # highlightbackground = "#0000FF",
        command=lambda:gui_int.destroy()

    )
    close_button.pack()

###################################
# Loading Data interface
###################################

def browse_button():
    filename = filedialog.askdirectory()
    return filename

def prep_config_file(wdw,dic,gui=True):
    dic_to_NMRFit = {
        'Data_Path'     :   dic['Data_Path'].get(),
        'Data_Folder'   :   dic['Data_Folder'].get(),
        'ExpNo'         :   dic['ExpNo'].get(),
        'ProcNo'        :   dic['ProcNo'].get(),
        'pdf_name'      :   dic['pdf_name'].get(),
        'Ref_Spec'      :   dic['Ref_Spec'].get(),
        'Data_Type'     :   dic['analysis_type'].get(),
        'Spec_Lim'      :   [float(i) for i in dic['Spec_Lim'].get().split(',')],
        'Threshold'     :   float(dic['Threshold'].get()),
        'pdf_path'      :   dic['pdf_path'].get(),
        'pdf_folder'    :   dic['pdf_folder'].get()
    }
    wdw.destroy()
    nmrr.run_analysis(dic_to_NMRFit, gui=gui)

def on_closing(wdw):
    wdw.destroy()
    exit()

# def ask_filename():
#     wdw = tk.Tk()
#     wdw.withdraw()
#     # the input dialog
#     file_name = simpledialog.askstring(
#         title="Config File Name",
#         prompt="Config Input File Name:",
#         initialvalue="Inputs_Spec_Fitting")
#     if file_name is None:
#         wdw.destroy()
#     else:
#         config_file = os.path.join(config_path,str(file_name)+'.json')
#         wdw.destroy()


def save_config_file(user_input):
    f = fd.askopenfilename()
    print(f)
    # dic_to_Save = {
    # 'Data_Path'         :   dic['Data_Path'].get(),
    # 'Data_Folder'       :   dic['Data_Folder'].get(),
    # 'Exp_Number'        :   dic['ExpNo'].get(),
    # 'ProcNo_Number'     :   dic['ProcNo'].get(),
    # 'pdf_name'          :   dic['pdf_name'].get(),
    # 'Ref_Spectrum'      :   dic['Ref_Spec'].get(),
    # 'Analysis_Type'     :   dic['analysis_type'].get(),
    # 'Specral_Region'    :   [float(i) for i in dic['Spec_Lim'].get().split(',')],
    # 'Threshold'         :   float(dic['Threshold'].get()),
    # 'pdf_path'          :   dic['pdf_path'].get(),
    # 'pdf_folder'        :   dic['pdf_folder'].get()
    # }
    # config_path = os.path.join(dic_to_Save['pdf_path'],dic_to_Save['pdf_folder'])
    # if not os.path.exists(config_path):
    #     os.makedirs(config_path)
    
    # # config_file = os.path.join(config_path,'Inputs_Spec_Fitting.txt')
    # # if os.path.exists(config_file):
    # ROOT = tk.Tk()
    # ROOT.withdraw()
    # # the input dialog
    # USER_INP = simpledialog.askstring(
    #     title="Config File Name",
    #     prompt="Config Input File Name:",
    #     initialvalue="Inputs_Spec_Fitting")
    # if USER_INP is None:
    #     ROOT.destroy()
    # else:
    #     config_file = os.path.join(config_path,str(USER_INP)+'.txt')
    #     ROOT.destroy()
    
    # cf_file = open(config_file,"w")
    # cf_file.write('## Config file created on '+str(date.today()))
    # cf_file.write('\n')
    # cf_file.write('##')
    # cf_file.write('\n')
    # for i in dic_to_Save.keys():
    #     if i is 'Specral_Region':
    #             cf_file.write('{}\t{},{}'.format(i, dic_to_Save[i][0],dic_to_Save[i][1]))
    #     else:
    #         cf_file.write('{}\t{}'.format(i, dic_to_Save[i]))
    #     cf_file.write('\n')

def create_entry(gui_wdw, label, x, y, width=210):
    # Label
    create_label(gui_wdw, label, x, y)

    # Entry
    if label == 'analysis_type':
        analysis_var = StringVar()
        analysis_options = ttk.Combobox(
            textvariable=analysis_var, 
            values=['1D','Pseudo2D','1D_Series'], 
            state="readonly"
        ).place(x=x, y=y+20, width=width)
        return analysis_var

    imput_var = StringVar()
    input_entry = Entry(gui_wdw,textvariable=imput_var)
    input_entry.place(x=x, y=y+20, width=width)

    return imput_var
    
def create_label(gui_wdw, label, x, y, font_size=14, font_weight='normal'):
    var_label = StringVar()
    Label(gui_wdw, textvariable=var_label,font=("Helvetica", font_size, font_weight),bg='#FFFFFF',fg='#8B0000',borderwidth=0).place(x=x, y=y)
    var_label.set(label.replace("_", " ").capitalize())

def load_config_file(user_input):
    
    config_file_path = fd.askopenfilename()
    if not config_file_path:
        return None

    try:
        f = open(config_file_path,"r")    
    except FileNotFoundError:
        error_interface('Config file not found')
        return None

    try:
        config = json.loads(f.read())
    except JSONDecodeError as e:
        error_interface('Json config file must be reformated')
        return None
    except UnicodeDecodeError as e:
        error_interface('Wrong config file type (not a json file, see example)')
        return None

    for label in user_input.keys():
        user_input[label].set(config.get(label, ''))


def start_gui():

    user_input = {
        'data_path':            [],
        'data_folder':          [],
        'data_exp_no':          [],
        'data_proc_no':         [],
        'analysis_type':        [],
        'reference_spectrum':   [],    
        'spectral_limits':      [],
        'threshold':            [],
        'output_path':          [],
        'output_folder':        [],    
        'output_name':          [],
    }

    gui_int = tk.Tk()
    gui_int.title("MultiNMRFit Interface")
    gui_int.geometry("700x600")
    gui_int.configure(bg='#FFFFFF')

    path_image = pkg_resources.resource_filename('multinmrfit', 'data/')
    # Set bottom picture
    img_network = Image.open(os.path.join(path_image, 'network.png'))
    img_network_ = ImageTk.PhotoImage(img_network.resize((700, 160))) 
    img_network_label = Label(gui_int, image = img_network_)
    img_network_label.place(x = 00, y = 440)

    # Import Logo
    img_logo = Image.open(os.path.join(path_image, 'logo_small.png'))
    img_logo_ = ImageTk.PhotoImage(img_logo.resize((300, 100))) 
    img_logo_logo = Label(gui_int,image=img_logo_)
    img_logo_logo.place(x = 200, y = 0)


    title = ['Inputs','Analysis','Outputs']
    i = 0
    for label in user_input.keys():
        x = 10 + int(i / 4) * 240
        y = 160 + int(i % 4) * 60
        if int(i%4) == 0:
            create_label(gui_int, title[int(i/4)], x + 50, 120, 18, 'bold')
        user_input[label] = create_entry(gui_int, label, x, y)
        i += 1

    ## ----- General Buttons ----- ##
    LoadButton = Button(
        gui_int,
        text=" Load ",
        fg='#FFFFFF',
        font=("Helvetica", 20),
        highlightbackground = "#8B0000",
        command=lambda:load_config_file(user_input)
        )
    LoadButton.place(x=20, y=400,width=80,height=30)
    
    SaveButton = Button(
        gui_int,
        text=" Save ",
        fg='#FFFFFF',
        font=("Helvetica", 20),
        highlightbackground = "#0000FF",
        command=lambda:save_config_file(dic_User_Input)
        )
    SaveButton.place(x=200, y=400,width=80,height=30)

    RunButton = Button(
        gui_int,
        text=" Run ",
        fg='#FFFFFF',
        font=("Helvetica", 20),
        highlightbackground = "#8B0000",
        command=lambda:prep_config_file(gui_int, dic_User_Input, gui=True)
    )
    RunButton.place(x=380, y=400,width=80,height=30)
    
    CloseButton = Button(
        gui_int,
        text=" Close ",
        fg='#FFFFFF',
        font=("Helvetica", 20),
        highlightbackground = "#0000FF",
        command=lambda:on_closing(gui_int)
        )
    CloseButton.place(x=560, y=400,width=80,height=30)
    
    # gui_int.protocol("WM_DELETE_WINDOW", on_closing(gui_int))
    #start gui interface
    gui_int.mainloop()
    
    #return dic_to_NMRFit

def start_cli():
    config_file = sys.argv[1]
    inputs_dic = read_config(config_file)
    nmrr.run_analysis(inputs_dic, gui=False)
    exit()

def read_config(config_file):
    user_inputs = pd.read_csv(config_file,sep='\t', header=1,names=['Var','User_Value']).set_index('Var')
    inputs_dic = {
        'Data_Path'         :   user_inputs.User_Value.Data_Path, 
        'Data_Folder'       :   user_inputs.User_Value.Data_Folder, 
        'Data_Type'         :   user_inputs.User_Value.Analysis_Type,
        'ExpNo'             :   int(user_inputs.User_Value.Exp_Number) if len(user_inputs.User_Value.Exp_Number) == 1 else user_inputs.User_Value.Exp_Number, 
        'ProcNo'            :   int(user_inputs.User_Value.ProcNo_Number), 
        'Ref_Spec'          :   int(user_inputs.User_Value.Ref_Spectrum), 
        'Spec_Lim'          :   [float(i) for i in user_inputs.User_Value.Specral_Region.split(',')],  
        'Threshold'         :   float(user_inputs.User_Value.Threshold),       
        'pdf_path'          :   user_inputs.User_Value.pdf_path,
        'pdf_folder'        :   user_inputs.User_Value.pdf_folder,        
        'pdf_name'          :   user_inputs.User_Value.pdf_name
        }
    return inputs_dic

