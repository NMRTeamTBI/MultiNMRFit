# Import system libraries
import pkg_resources
import random
import json
import sys
import os 
import logging
import argparse
from pathlib import Path

# Import display libraries
import tkinter as tk
from tkinter import simpledialog, ttk, filedialog
from PIL import Image, ImageTk

# Import plot libraries
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages

# Import math libraries
import pandas as pd
import numpy as np

# Import our own libraries
import multinmrfit.run as nmrr
import multinmrfit.multiplets as nmrm
import multinmrfit.fitting as nmrf

matplotlib.use("TkAgg")

tk_wdw = None 
logger = logging.getLogger()

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
    Res.Peak_Amp = dic['Peak Intensity']
    Res.ppm_H_AXIS = dic['Peak Position']
    Res.Options = [i.get() for i in dic["Options"]]
    Res.Cluster = [i.get() for i in dic["Cluster ID"]]
    Res.Selection = [True if i.get() != '' else False for i in dic["Cluster ID"]]
    r.destroy()
    plt.close()

def refresh_threshold(r, dic, updated_threshold):
    for n in dic['th']:
        nt = n.get()
    updated_threshold.nt.loc[1] = nt
    r.destroy()
    plt.close()
    return updated_threshold

def Exit(r):
    r.destroy()
    plt.close()
    exit()

def wdw_peak_picking(peak_picking_threshold, peak_picking_data, figure, colors, Res, updated_threshold):

    wdw = tk.Tk()
    wdw.title('Peak Picking Visualisation and Validation')

    graph = FigureCanvasTkAgg(figure, master=wdw)
    canvas = graph.get_tk_widget()
    canvas.grid(row=0, column=0,columnspan = 8,rowspan=1)

    list_of_options=['Roof'] # options
    
    user_input = {
        'Peak Position'    :   [],
        'Peak Intensity'   :   [],
        'Cluster ID'       :   [],
        'Options'          :   []
    }

    c = 0 
    for label in user_input.keys():
        tk.Label(
            wdw, 
            text=label, 
            font=("Helvetica", 14, 'bold')
        ).grid(column=c+1, row=2)
        c +=1

    dic_par = {'th'    :   []}
    npeaks = len(peak_picking_data)
    for i in range(npeaks):
        tk.Label(wdw, text="Peak "+str(i+1),fg=colors[i]).grid(column=0, row=i+3)
        tk.Entry(wdw,justify = "center")
       
        # Clustering
        cluster_entry = tk.Entry(wdw,justify = "center")
        user_input['Cluster ID'].append(cluster_entry)
        cluster_entry.grid(row=i+3,column=3)

        options_entry = ttk.Combobox(wdw, values=list_of_options)
        user_input['Options'].append(options_entry)
        options_entry.grid(row=i+3,column=4)
        for col in peak_picking_data.columns:
            en_c = tk.Entry(wdw,justify = "center")
            data = peak_picking_data.iloc[i].loc[col]
            if col == 'ppm_H_AXIS':
                user_input['Peak Position'].append(data)
                cc = 0
            if col == 'Peak_Amp':
                user_input['Peak Intensity'].append(data)
                cc = 1
            en_c.insert(0, round(data,3))
            en_c.grid(column=cc+1,row=i+3)
    
    disp = tk.Entry(wdw, readonlybackground="white")
    tk.Label(
        wdw, 
        text="Threshold", 
        font=("Helvetica", 14, 'bold'), fg='#f00'
    ).grid(column=0, row=1)

    disp.insert(0, peak_picking_threshold)
    disp.grid(column=1, row=1)
    dic_par['th'].append(disp)

    tk.Button(
        wdw, 
        text="Refresh & Close", 
        fg = "orange", 
        font=("Helvetica", 20),        
        command=lambda: refresh_threshold(wdw, dic_par, updated_threshold)
    ).grid(column = 0, row = npeaks+3)  
    
    tk.Button(
        wdw, 
        text="Save & Close", 
        fg = "blue", 
        font=("Helvetica", 20),        
        command=lambda: save_info_clustering(wdw, user_input, Res)
    ).grid(column = 1, row = npeaks+3) 

    tk.Button(
        wdw, 
        text="Exit", 
        fg = "black", 
        font=("Helvetica", 20),        
        command=lambda: Exit(wdw)
    ).grid(column = 2, row = npeaks+3) 

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
    return Res

def plot_picking_data(x_spec, y_spec, peak_picking_threshold, peak_picking_data):
    n_peak = len(peak_picking_data)

    # Create a list of colors
    colors = []
    for i in range(n_peak):
        colors.append('#%06X' % random.randint(0, 0xFFFFFF))

    fig = plt.figure()
    plt.plot(x_spec, y_spec, '-',color='teal')
    for i in range(n_peak):
        plt.plot(
            peak_picking_data.ppm_H_AXIS.iloc[i],
            peak_picking_data.Peak_Amp.iloc[i],
            c=colors[i],
            ls='none',
            marker='o'
            )
    plt.axhline(peak_picking_threshold,c='r')
    plt.gca().invert_xaxis()
    plt.xlabel(r'$^1H$ $(ppm)$')
    return fig, colors 

def run_peak_picking(x_spec,y_spec,peak_picking_threshold,peak_picking_data):


    clustering_results = initialize_results_clustering()
    updated_threshold = pd.DataFrame(columns=['nt'],index=[1])

    fig, colors = plot_picking_data(
        x_spec, 
        y_spec, 
        peak_picking_threshold, 
        peak_picking_data
    )

    wdw_peak_picking(
        peak_picking_threshold,
        peak_picking_data, 
        fig,
        colors,
        clustering_results,
        updated_threshold
    )
    clustering_results = filter_multiple_clusters(clustering_results)
    return updated_threshold, clustering_results

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

def error_interface(message, critical_error=False):
    if tk_wdw:
        error_window = tk.Tk()
        error_window.title("Error")
        error_window.configure(bg='#FFFFFF')

        label = tk.Label(error_window, text=message, font=("Helvetica",18),bg='#FFFFFF',borderwidth=20)
        label.pack()

        close_button = tk.Button(
            error_window,
            text="Close ",
            # fg='#FFFFFF',
            font=("Helvetica", 14),
            # highlightbackground = "#0000FF",
            command=lambda:error_window.destroy()

        )
        close_button.pack()
    elif logger:
        logger.error(message)
    
    if critical_error:
        exit(1)

###################################
# Loading Data interface
###################################
def create_experiments_list(user_input):
    Exp_List = []
    for i in user_input.get('data_exp_no').split(','):
        if "-" in i:
            spectra = i.split('-')
            Exp_List += range(int(spectra[0]), int(spectra[1])+1)
        else:
            Exp_List.append(int(i))
    return Exp_List

def check_path(path):
    """
    check if 'path' exists, and create it if it doesn't exist
    """
    sub_path = os.path.dirname(path)
    if not os.path.exists(sub_path):
        check_path(sub_path)
    if not os.path.exists(path):
        os.mkdir(path)

def launch_analysis(user_input):
    is_gui = (tk_wdw != None)
    is_not_gui = (tk_wdw == None)

    try:
        output_dir = os.path.join(user_input.get('output_path'),user_input.get('output_folder'))
        if not output_dir:
            return error_interface("Argument : 'output_folder' is missing", critical_error=is_not_gui)

        if not Path(output_dir).exists():
            check_path(output_dir)

        # create logger (should be root to catch builder and simulator loggers)
        # logger = logging.getLogger()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
        # sends logging output to 'process_log.txt' file
        file_handler = logging.FileHandler(str(Path(output_dir, "process_log.txt")), mode='w+')
        file_handler.setFormatter(formatter)
        # sends logging output to sys.stderr
        strm_handler = logging.StreamHandler()
        strm_handler.setFormatter(formatter)
        # add handlers to logger
        logger.addHandler(strm_handler)
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)

        if not Path(user_input.get('data_path')).exists():
            return error_interface("Argument : 'data_path' does not exist", critical_error=is_not_gui)

        if not Path(user_input.get('data_path'),user_input.get('data_folder')).exists():
            return error_interface("Argument : 'data_folder' does not exist", critical_error=is_not_gui)

        if float(user_input.get('threshold', 1)) <= float(0):
            return error_interface("Argument : 'threshold' is too low (should be > 0)", critical_error=is_not_gui)

        if user_input.get('analysis_type') not in ['Pseudo2D', '1D', '1D_Series']:
            return error_interface("Argument : 'analysis_type' expected as 'Pseudo2D','1D' or '1D_Series", critical_error=is_not_gui)

        if not user_input.get('spectral_limits'):
            return error_interface("Argument : 'spectral_limits' is missing" , critical_error=is_not_gui)

        spec_lim = [float(i) for i in user_input.get('spectral_limits').split(',')]

        if len(spec_lim)%2 != 0 and len(spec_lim) != 0:
            return error_interface("Argument : 'spectral_limits' is incomplete", critical_error=is_not_gui)

        exp_list = create_experiments_list(user_input)
        for exp in exp_list:
            if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp)).exists():
                return error_interface(f"Argument : experiment <{exp}> does not exist", critical_error=is_not_gui)
            else:
                if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp),'pdata',user_input.get('data_proc_no')).exists():
                    return error_interface(f"Argument : experiment/procno <{exp}/{user_input.get('data_proc_no')}> does not exist", critical_error=is_not_gui)

        if int(user_input.get('reference_spectrum')) not in exp_list:
            return error_interface(f"Argument : reference_spectrum <{user_input.get('reference_spectrum')}> not found in experiment list", critical_error=is_not_gui)

        config = {
            'data_path'             :   user_input.get('data_path'),
            'data_folder'           :   user_input.get('data_folder'),
            'data_exp_no'           :   exp_list,
            'data_proc_no'          :   user_input.get('data_proc_no'),####
            'reference_spectrum'    :   user_input.get('reference_spectrum'),
            'analysis_type'         :   user_input.get('analysis_type'),
            'spectral_limits'       :   spec_lim,
            'threshold'             :   float(user_input.get('threshold', 0)),
            'output_path'           :   user_input.get('output_path'),
            'output_folder'         :   user_input.get('output_folder'),
            'output_name'           :   user_input.get('output_name'),

        }
    except Exception as e:
        return error_interface(e, critical_error=is_not_gui)
    for key, conf in config.items():
        if not conf:
            return error_interface(f"Argument : '{key}' is missing", critical_error=is_not_gui)
    if is_gui:
        tk_wdw.destroy()
    logger.info(json.dumps(config,indent=4))
    nmrr.run_analysis(config, gui = is_gui)

def on_closing():
    tk_wdw.destroy()
    exit(0)

def ask_filename(config_path):
    wdw = tk.Tk()
    wdw.withdraw()
    # the input dialog
    file_name = simpledialog.askstring(
        title="Config File Name",
        prompt="Config Input File Name:",
        initialvalue="Inputs_Spec_Fitting")
    if file_name is None:
        wdw.destroy()
    else:
        config_file = os.path.join(config_path,str(file_name)+'.json')
        wdw.destroy()
    return config_file

def save_config_file(user_input):
    config_path = os.path.join(user_input['output_path'], user_input['output_folder'])
    file_name = ask_filename(config_path)
    f = open(file_name, "a")
    f.seek(0)
    f.truncate()
    f.write(json.dumps(user_input, indent=4))
    f.close()    

def create_entry(label, x, y, width=210):
    # Label
    create_label(label, x, y)

    # Entry
    if label == 'analysis_type':
        analysis_var = tk.StringVar()
        analysis_options = ttk.Combobox(
            textvariable=analysis_var, 
            values=['1D','Pseudo2D','1D_Series'], 
            state="readonly"
        ).place(x=x, y=y+20, width=width)
        return analysis_var

    imput_var = tk.StringVar()
    input_entry = tk.Entry(textvariable=imput_var)
    input_entry.place(x=x, y=y+20, width=width)

    return imput_var
    
def create_label(label, x, y, font_size=14, font_weight='normal'):
    tk.Label(
        tk_wdw,
        text=label.replace("_", " ").capitalize(),
        font=("Helvetica", font_size, font_weight),
        bg='#FFFFFF',
        fg='#8B0000',
        borderwidth=0
    ).place(x=x, y=y)

def load_config_file(user_input=None, config_file_path=None):
    if tk_wdw:
        config_file_path = filedialog.askopenfilename()    
        if not config_file_path:
            return None

    try:
        f = open(config_file_path,"r")    
    except FileNotFoundError:
        error_interface('Config file not found')
        return None

    try:
        config = json.loads(f.read())
    except json.decoder.JSONDecodeError as e:
        error_interface('Json config file must be reformated')
        return None
    except UnicodeDecodeError as e:
        error_interface('Wrong config file type (not a json file, see example)')
        return None

    if tk_wdw:
        for label in user_input.keys():
            user_input[label].set(config.get(label, ''))
        return user_input
    else:
        return config

def start_gui():

    user_input = {
        'data_path':            None,
        'data_folder':          None,
        'data_exp_no':          None,
        'data_proc_no':         None,
        'analysis_type':        None,
        'reference_spectrum':   None,    
        'spectral_limits':      None,
        'threshold':            None,
        'output_path':          None,
        'output_folder':        None,    
        'output_name':          None,
    }
    global tk_wdw
    tk_wdw = tk.Tk()
    tk_wdw.title("MultiNMRFit Interface")
    tk_wdw.geometry("700x600")
    tk_wdw.configure(bg='#FFFFFF')

    path_image = pkg_resources.resource_filename('multinmrfit', 'data/')
    # Set bottom picture
    img_network = Image.open(os.path.join(path_image, 'network.png'))
    img_network_ = ImageTk.PhotoImage(img_network.resize((700, 160))) 
    img_network_label = tk.Label(tk_wdw, image = img_network_)
    img_network_label.place(x = 00, y = 440)

    # Import Logo
    img_logo = Image.open(os.path.join(path_image, 'logo_small.png'))
    img_logo_ = ImageTk.PhotoImage(img_logo.resize((300, 100))) 
    img_logo_logo = tk.Label(tk_wdw,image=img_logo_)
    img_logo_logo.place(x = 200, y = 0)


    title = ['Inputs','Analysis','Outputs']
    i = 0
    for label in user_input.keys():
        x = 10 + int(i / 4) * 240
        y = 160 + int(i % 4) * 60
        if int(i%4) == 0:
            create_label(title[int(i/4)], x + 50, 120, 18, 'bold')
        user_input[label] = create_entry(label, x, y)
        i += 1

    ## ----- General Buttons ----- ##
    LoadButton = tk.Button(
        tk_wdw,
        text=" Load ",
        fg='#FFFFFF',
        font=("Helvetica", 20),
        highlightbackground = "#8B0000",
        command=lambda:load_config_file(user_input)
        )
    LoadButton.place(x=20, y=400,width=80,height=30)
    
    SaveButton = tk.Button(
        tk_wdw,
        text=" Save ",
        fg='#FFFFFF',
        font=("Helvetica", 20),
        highlightbackground = "#0000FF",
        command=lambda:save_config_file({k: v.get() for k, v in user_input.items()})
        )
    SaveButton.place(x=200, y=400,width=80,height=30)

    RunButton = tk.Button(
        tk_wdw,
        text=" Run ",
        fg='#FFFFFF',
        font=("Helvetica", 20),
        highlightbackground = "#8B0000",
        command=lambda:launch_analysis({k: v.get() for k, v in user_input.items()})
    )
    RunButton.place(x=380, y=400,width=80,height=30)
    
    CloseButton = tk.Button(
        tk_wdw,
        text=" Close ",
        fg='#FFFFFF',
        font=("Helvetica", 20),
        highlightbackground = "#0000FF",
        command=lambda:on_closing()
        )
    CloseButton.place(x=560, y=400,width=80,height=30)
    
    tk_wdw.mainloop()
    

def start_cli():
    if not len(sys.argv) == 2:
        error_interface('usage: multinmrfitcli <path/config/file>  ', critical_error=True)
    user_input = load_config_file(config_file_path=sys.argv[1])
    if not user_input:
        exit(1)
    launch_analysis(user_input)
    exit()


