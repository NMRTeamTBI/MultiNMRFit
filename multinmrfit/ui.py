# Import system libraries
from tkinter.constants import N
import pkg_resources
import random
import json
import sys
import os 
import logging
import argparse
import threading
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path 
import customtkinter 
#https://github.com/TomSchimansky/CustomTkinter
# customtkinter.set_appearance_mode("System")
# customtkinter.set_default_color_theme("dark-blue")

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
import multinmrfit.multiplets as nfm
import multinmrfit.fitting as nff

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

def save_info_clustering(dic, Res):
    Res.Peak_Intensity = dic['Peak Intensity']
    Res.Peak_Position = dic['Peak Position']
    Res.Options = [i.get() for i in dic["Options"]]
    Res.Cluster = [i.get() for i in dic["Cluster ID"]]
    Res.Selection = [True if i.get() != '' else False for i in dic["Cluster ID"]]
    tk_wdw.destroy()
    plt.close()

def refresh_ui(refreshed_threshold, threshold_entry):
    refreshed_threshold["th"] = threshold_entry.get()
    tk_wdw.destroy()
    plt.close()

def Exit():
    if tk.messagebox.askokcancel("quit",'Do you want to quit?'):
        tk_wdw.destroy()
        plt.close()
        exit()

def user_clustering_gui(peak_picking_threshold, peak_picking_data, figure, colors, Res):
    global tk_wdw
    tk_wdw = tk.Tk()
    tk_wdw.protocol("WM_DELETE_WINDOW", Exit)
    tk_wdw.title('Peak Picking Visualisation and Validation')

    graph = FigureCanvasTkAgg(figure, master=tk_wdw)
    canvas = graph.get_tk_widget()
    canvas.grid(row=0, column=0,columnspan = 8,rowspan=1)

    list_of_options=['Roof'] # options
    
    user_input = {
        'Peak Position'    :   [],
        'Peak Intensity'   :   [],
        'Cluster ID'       :   [],
        'Options'          :   []
    }

    npeaks = len(peak_picking_data)
    if not npeaks:
        tk.Label(
            tk_wdw, 
            text='No peak found, please lower the threshold',
            font=("Helvetica", 14, 'bold'),
            fg='#f00'
        ).grid(column=0, row=3)
        tk.Entry(tk_wdw,justify = "center")
    else:
        c = 0 
        for label in user_input.keys():
            tk.Label(
                tk_wdw, 
                text=label, 
                font=("Helvetica", 14, 'bold')
            ).grid(column=c+1, row=2)
            c +=1

        for i in range(npeaks):
            tk.Label(tk_wdw, text="Peak "+str(i+1),fg=colors[i]).grid(column=0, row=i+3)
            tk.Entry(tk_wdw,justify = "center")
        
            # Clustering
            cluster_entry = tk.Entry(tk_wdw,justify = "center")
            user_input['Cluster ID'].append(cluster_entry)
            cluster_entry.grid(row=i+3,column=3)

            options_entry = ttk.Combobox(tk_wdw, values=list_of_options)
            user_input['Options'].append(options_entry)
            options_entry.grid(row=i+3,column=4)
            for col in peak_picking_data.columns:
                en_c = tk.Entry(tk_wdw,justify = "center")
                data = peak_picking_data.iloc[i].loc[col]
                if col == 'Peak_Position':
                    user_input['Peak Position'].append(data)
                    cc = 0
                if col == 'Peak_Intensity':
                    user_input['Peak Intensity'].append(data)
                    cc = 1
                en_c.insert(0, round(data,3))
                en_c.grid(column=cc+1,row=i+3)
    
    tk.Label(
        tk_wdw, 
        text="Threshold", 
        font=("Helvetica", 14, 'bold'), fg='#f00'
    ).grid(column=0, row=1)

    threshold_entry = tk.Entry(tk_wdw, readonlybackground="white")
    threshold_entry.insert(0, peak_picking_threshold)
    threshold_entry.grid(column=1, row=1)
    refreshed_threshold = { "th" : None }

    tk.Button(
        tk_wdw, 
        text="Refresh & Close", 
        fg = "orange", 
        font=("Helvetica", 20),        
        command=lambda: refresh_ui(refreshed_threshold, threshold_entry)
    ).grid(column = 0, row = npeaks+3 if npeaks else 4)  
    
    tk.Button(
        tk_wdw, 
        text="Save & Close", 
        fg = "blue", 
        font=("Helvetica", 20),        
        command=lambda: save_info_clustering(user_input, Res)
    ).grid(column = 1, row = npeaks+3 if npeaks else 4) 

    tk.Button(
        tk_wdw, 
        text="Exit", 
        fg = "black", 
        font=("Helvetica", 20),        
        command=lambda: Exit()
    ).grid(column = 2, row = npeaks+3 if npeaks else 4) 

    tk_wdw.mainloop()
    if refreshed_threshold["th"]:
        return float(refreshed_threshold["th"])
    else:
        return None

def filter_multiple_clusters(Res):
    for i,j in enumerate(Res.Cluster):
        cluster_num = j.split(',')
        if len(cluster_num) > 1:
            for k in cluster_num:
                new_pk = {'Peak_Position': Res.iloc[i].ppm_H_AXIS,'Peak_Intensity': Res.iloc[i].Peak_Amp,'Selection': Res.iloc[i].Selection,'Cluster': k}
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
            peak_picking_data.Peak_Position.iloc[i],
            peak_picking_data.Peak_Intensity.iloc[i],
            c=colors[i],
            ls='none',
            marker='o'
            )
    plt.axhline(peak_picking_threshold,c='r')
    plt.gca().invert_xaxis()
    plt.xlabel(r'$^1H$ $(ppm)$')
    return fig, colors 

def run_user_clustering(figures, colors_plot, peak_picking_threshold, peak_picking_data):

    clustering_results = pd.DataFrame(columns=['Peak_Position','Peak_Intensity','Selection','Cluster','Options'])

    refreshed_threshold = user_clustering_gui(
        peak_picking_threshold,
        peak_picking_data, 
        figures,
        colors_plot,
        clustering_results
    )

    clustering_results = filter_multiple_clusters(clustering_results)
    return refreshed_threshold, clustering_results

###################################
# Final Plots
###################################

def getList(dict):
    return [k for k in dict.keys()]

def getIntegral(x_fit_, _multiplet_type_, fit_par):
    d_mapping = nfm.mapping_multiplets()[0]
    _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
    y = _multiplet_type_function(x_fit_, *fit_par)
    integral = np.sum(y)*(x_fit_[1]-x_fit_[0])
    return integral

def single_plot_function(r, x_scale, intensities, fit_results, x_fit, d_id, scaling_factor, analysis_type, output_path, output_folder,output_name,i=None):    
    fig, ax = plt.subplots(1, 1)
    fig.set_size_inches([11.7,8.3])
    ax.plot(
        x_scale,
        intensities[r if analysis_type == 'Pseudo2D' else i ,:],
        color='b',
        ls='None',
        marker='o',
        markersize=7
        )    
    ax.invert_xaxis()
    res = fit_results.loc[r if analysis_type == 'Pseudo2D' else i ].iloc[:].values.tolist()

    sim = nff.simulate_data(
        x_fit,
        res,
        d_id,
        scaling_factor
        )

    ax.plot(
        x_fit, 
        sim, 
        'r-', 
        lw=1,
        label='fit')

    res_num = r+1 if analysis_type == 'Pseudo2D' else r
    ax.text(0.05,0.9,"Spectra : " +str(res_num),transform=ax.transAxes,fontsize=20)  
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
    path_2_save = Path(output_path,output_folder,'plot_ind')
    path_2_save.mkdir(parents=True,exist_ok=True)

    plt.savefig(str(Path(path_2_save,output_name+'_'+str(res_num)+'.pdf')))
    plt.close(fig)

def save_output_data(
    user_input         = 'user_input',
    fit_results         = 'fit_results', 
    intensities         = 'intensities',    
    x_scale             = 'x_scale',
    spectra_to_fit      =  'spectra_to_fit',
    Peak_Picking_data   =  None,
    scaling_factor      =  None
    ):

    output_path         =   user_input['output_path']
    output_folder       =   user_input['output_folder']
    output_name         =   user_input['output_name']
    analysis_type       =   user_input['analysis_type']
    data_exp_no         =   user_input['data_exp_no']

    logger.info('Save data to text file ')

    x_fit = np.linspace(np.min(x_scale),np.max(x_scale),2048)
    d_id = nff.Initial_Values(Peak_Picking_data, x_fit, scaling_factor)[0]

    cluster_list = getList(d_id)

    Fit_results = fit_results.apply(pd.to_numeric)
    Fit_results_text= Fit_results.round(9)

    Path(output_path,output_folder).mkdir(parents=True,exist_ok=True)
    
    d_mapping, _, d_parameters = nfm.mapping_multiplets()

    for i in cluster_list:        
        #Check ifoutput file exists 

        col = range(d_id[i][1][0],d_id[i][1][1])
        _multiplet_type_ = d_parameters[len(col)]
        _multiplet_params_ = d_mapping[_multiplet_type_]['params']

        mutliplet_results = Fit_results_text[Fit_results_text.columns.intersection(col)]
  
        mutliplet_results.columns = _multiplet_params_

        mutliplet_results["integral"] = [scaling_factor*getIntegral(x_fit, _multiplet_type_, row.tolist()) for index, row in mutliplet_results.iterrows()]
        mutliplet_results["Amp"] = scaling_factor*mutliplet_results["Amp"]

        if analysis_type == 'Pseudo2D':
            mutliplet_results.insert(loc = 0, column = 'exp_no' , value = np.array([data_exp_no]*len(spectra_to_fit)))
            mutliplet_results.insert(loc = 1, column = 'row_id' , value = spectra_to_fit)
        elif analysis_type == '1D_Series':
            mutliplet_results.insert(loc = 0, column = 'exp_no' , value = spectra_to_fit)
            mutliplet_results.insert(loc = 1, column = 'row_id' , value = [1]*len(spectra_to_fit))

        mutliplet_results.set_index('exp_no', inplace=True)
        mutliplet_results.to_csv(
            str(Path(output_path,output_folder,output_name+'_'+str(_multiplet_type_)+'_'+str(i)+'.txt')), 
            index=True, 
            sep = '\t'
            )
    logger.info('Save data to text file -- Complete')

    logger.info('Save plot to pdf')

    
    # root, close_button, progress_bars = init_progress_bar_windows(len_progresses = [len(speclist)],title='Output data in pdf',progress_bar_label=[None]) 

    for r in spectra_to_fit:
        if analysis_type == '1D_Series':
            i = spectra_to_fit.index(r)
        single_plot_function(
                r, 
                x_scale, 
                intensities,        
                fit_results, 
                x_fit, 
                d_id, 
                scaling_factor, 
                analysis_type,
                output_path,   
                output_folder,
                output_name,
                i  
            )
            
    # with PdfPages(Path(output_path,output_folder,output_name+'.pdf')) as pdf:   
    #     matplotlib.pyplot.switch_backend('Agg') 
    #     for r in range(len(speclist)):
    #         single_plot_function(
    #             r, 
    #             pdf, 
    #             x_scale, 
    #             intensities,        
    #             fit_results, 
    #             x_fit, 
    #             d_id, 
    #             scaling_factor, 
    #             id_spectra, 
    #             speclist
    #         )    

        # threads = []
        # threads.append(MyApp_Plotting(data={
        #     'speclist'              : speclist,
        #     'pdf'                   : pdf, 
        #     'x_scale'               : x_scale, 
        #     'intensities'           : intensities,       
        #     'fit_results'           : fit_results, 
        #     'x_fit'                 : x_fit, 
        #     'd_id'                  : d_id, 
        #     'scaling_factor'        : scaling_factor, 
        #     'id_spectra'            : id_spectra

        # },
        # threads=threads,
        # close_button=close_button,
        # progressbar=progress_bars[0]
        # ))
        # root.mainloop()
    logger.info('Save plot to pdf -- Complete')

    
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
    experiment_list = []
    for i in user_input.split(','):
        if "-" in i:
            spectra = i.split('-')
            experiment_list += range(int(spectra[0]), int(spectra[1])+1)
        else:
            experiment_list.append(int(i))
    return experiment_list

# def check_path(path):
#     """
#     check if 'path' exists, and create it if it doesn't exist
#     """
#     sub_path = os.path.dirname(path)
#     if not os.path.exists(sub_path):
#         check_path(sub_path)
#     if not os.path.exists(path):
#         os.mkdir(path)

def launch_analysis(user_input):
    is_gui = (tk_wdw != None)
    is_not_gui = (tk_wdw == None)

    try:
        output_dir = Path(user_input.get('output_path'),user_input.get('output_folder'))
        # if not output_dir:
        #     return error_interface("Argument : 'output_folder' is missing", critical_error=is_not_gui)

        output_dir.mkdir(parents=True,exist_ok=True)

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

        exp_list = create_experiments_list(user_input.get('data_exp_no'))
        for exp in exp_list:
            if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp)).exists():
                return error_interface(f"Argument : experiment <{exp}> does not exist", critical_error=is_not_gui)
            else:
                if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp),'pdata',user_input.get('data_proc_no')).exists():
                    return error_interface(f"Argument : experiment/procno <{exp}/{user_input.get('data_proc_no')}> does not exist", critical_error=is_not_gui)
        if user_input.get('analysis_type') != 'Pseudo2D' and int(user_input.get('reference_spectrum')) not in exp_list:
            return error_interface(f"Argument : reference_spectrum <{user_input.get('reference_spectrum')}> not found in experiment list", critical_error=is_not_gui)

        row_list = []
        if user_input.get('data_row_no'):
            row_list = create_experiments_list(user_input.get('data_row_no'))
            if int(user_input.get('reference_spectrum')) not in row_list :
                return error_interface(f"Argument : reference_spectrum <{user_input.get('reference_spectrum')}> not found in row list", critical_error=is_not_gui)

        config = {
            'data_path'             :   user_input.get('data_path'),
            'data_folder'           :   user_input.get('data_folder'),
            'data_exp_no'           :   exp_list,
            'data_proc_no'          :   user_input.get('data_proc_no'),
            'data_row_no'           :   row_list,
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
        if conf is None:
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
        config_file = Path(config_path,str(file_name)+'.json')
        wdw.destroy()
    return config_file

def save_config_file(user_input):
    config_path = Path(user_input['output_path'], user_input['output_folder'])
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
        ttk.Combobox(
            textvariable=analysis_var, 
            values=['1D','Pseudo2D','1D_Series'], 
            state="readonly"
        ).place(x=x, y=y+30, width=width)
        return analysis_var

    imput_var = tk.StringVar()
    input_entry = customtkinter.CTkEntry(textvariable=imput_var,corner_radius=8)
    input_entry.place(x=x, y=y+30, width=width)

    return imput_var

def create_label(label, x, y):
    customtkinter.CTkLabel(
        tk_wdw,
        text=label.replace("_", " ").capitalize(),
        corner_radius=8,
        borderwidth=0,
        justify=tk.CENTER
    ).place(x=x, y=y)

def load_config_file(user_input=None, config_file_path=None):
    if tk_wdw:
        config_file_path = filedialog.askopenfilename()    
        if not config_file_path:
            return None

    try:
        f = open(str(Path(config_file_path)),"r")    
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
        'rows_pseudo2D':         None,

    }
    global tk_wdw
    tk_wdw = customtkinter.CTk()
    tk_wdw.title("Multinmrfit Interface")
    tk_wdw.geometry("950x650")
    #tk_wdw.configure(bg='#FFFFFF')

    path_image = pkg_resources.resource_filename('multinmrfit', 'data/')
    # Set bottom picture
    img_network = Image.open(str(Path(path_image, 'network.png')))
    img_network_ = ImageTk.PhotoImage(img_network.resize((950, 160))) 
    img_network_label = tk.Label(tk_wdw, image = img_network_)
    img_network_label.place(x = 00, y = 490)

    # Import Logo
    img_logo = Image.open(str(Path(path_image, 'logo_small.png')))
    img_logo_ = ImageTk.PhotoImage(img_logo.resize((300, 100))) 
    img_logo_logo = tk.Label(tk_wdw,image=img_logo_)
    img_logo_logo.place(x = 300, y = 0)

    title = ['Inputs','Analysis','Outputs']
    i = 0
    n_row = 4 
    for label in user_input.keys():
        x = 10 + int(i / n_row) * 240
        y = 160 + int(i % n_row) * 70
        if int(i/n_row) != 3:
            if int(i%n_row) == 0:
                create_label(title[int(i/n_row)], x + 50, 120)
        user_input[label] = create_entry(label, x, y)
        if label is 'output_name':
            i += 2
        else:
            i += 1

    #CheckBox
    check_box_1 = customtkinter.CTkCheckBox(
        tk_wdw,
        text="Options")
    check_box_1.place(
        x=850, 
        y=120, 
        anchor=tk.CENTER
        )

    ## ----- General Buttons ----- ##
    LoadButton = customtkinter.CTkButton(
        tk_wdw,
        text=" Load ",
        #fg='#FFFFFF',
        #font=("Helvetica", 20),
        corner_radius=10,
#        highlightbackground = "#8B0000",
        command=lambda:load_config_file(user_input)
        )
    LoadButton.place(x=20, y=440,width=80,height=30)
    
    SaveButton = customtkinter.CTkButton(
        tk_wdw,
        text=" Save ",
        #fg='#FFFFFF',
        #font=("Helvetica", 20),
        corner_radius=10,
#        highlightbackground = "#0000FF",
        command=lambda:save_config_file({k: v.get() for k, v in user_input.items()})
        )
    SaveButton.place(x=200, y=440,width=80,height=30)

    RunButton = customtkinter.CTkButton(
        tk_wdw,
        text=" Run ",
        #fg='#FFFFFF',
        #font=("Helvetica", 20),
        corner_radius=10,
        #highlightbackground = "#8B0000",
        command=lambda:launch_analysis({k: v.get() for k, v in user_input.items()})

    )
    RunButton.place(x=380, y=440,width=80,height=30)
    
    CloseButton = customtkinter.CTkButton(
        tk_wdw,
        text=" Close ",
        #fg='#FFFFFF',
        #font=("Helvetica", 20),
        corner_radius=10,
        #highlightbackground = "#0000FF",
        command=lambda:on_closing()
        )
    CloseButton.place(x=560, y=440,width=80,height=30)
    
    tk_wdw.mainloop()

###################################
# Progress bars
###################################

def progress_bar_exit(root):
    root.destroy()

# def progress_label(progress_bar):
#     return f"Current Progress: {progress_bar['value']}%"


def init_progress_bar_windows(len_progresses, title, progress_bar_label):
    root = tk.Tk()
    root_height= len(len_progresses)*120
    root.geometry(f'300x{root_height}')
    root.title(title)

    progress_bars = []
    for len_progress in len_progresses:
        pg_bar = ttk.Progressbar(
            root,
            orient='horizontal',
            mode='determinate',
            maximum=len_progress,
            length=280
        )

        # value_label = ttk.Label(root, text=update_progress_label())
        value_label = ttk.Label(root, text=progress_bar_label[len(progress_bars)])
        value_label.grid(column=0, row=len(len_progresses)*len(progress_bars), columnspan=2)

        pg_bar.grid(column=0, row=len(len_progresses)*len(progress_bars)+1, columnspan=2, padx=10, pady=20)
        progress_bars.append(pg_bar)


    close_button = tk.Button(
        root, 
        text="Close", 
        fg = "black", 
        font=("Helvetica", 20),        
        command=lambda: progress_bar_exit(root)
    )
    close_button.grid(column = 1, row = len(len_progresses)+5)
    return root, close_button, progress_bars


class MyApp_Fitting(threading.Thread):

    def __init__(self, data, threads, close_button, progressbar):
        self.finished = False
        self.threads = threads
        self.data = data
        self.close_button = close_button
        # self.progress_label = progress_label
        self.progressbar = progressbar
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        for fit in self.data["spec_list"]:
            self.progressbar["value"] += 1
            # self.progress_label["value"] +=1
            nff.run_single_fit_function(fit=fit, **self.data)
        self.finished = True
        finished = True
        for thread in self.threads:
            finished = thread.finished if thread.finished == False else finished
        if finished:
            self.close_button.invoke()

class MyApp_Plotting(threading.Thread):
    def __init__(self, data, threads, close_button, progressbar):
        self.finished = False
        self.threads = threads
        self.data = data
        self.close_button = close_button
        self.progressbar = progressbar
        threading.Thread.__init__(self)
        self.start()

    def run(self):
        for r in self.data["speclist"]:
            single_plot_function(r = r, **self.data)
            self.progressbar["value"] += 1
        
        self.finished = True
        finished = True
        for thread in self.threads:
            finished = thread.finished if thread.finished == False else finished
        if finished:
            self.close_button.invoke()

