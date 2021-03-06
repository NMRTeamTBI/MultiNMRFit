from re import L
import tkinter
import tkinter.messagebox
import random

import sys
import json
from pathlib import Path 
import tkinter as tk
from tkinter import simpledialog, ttk, messagebox
import logging
import webbrowser
import urllib.request as urlrequest
import re
import threading

# Import plot libraries
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import multinmrfit
import multinmrfit.io as nio
import multinmrfit.run as nrun
import multinmrfit.utils_nmrdata as nfu

# initialize logger
logger = logging.getLogger(__name__)

def openDoc():
    webbrowser.open_new(r"https://multinmrfit.readthedocs.io/en/latest/")

def openGit():
    webbrowser.open_new(r"https://github.com/NMRTeamTBI/MultiNMRFit/")

def check_up_to_date():
    """Compare local and distant MultiNMRFit versions."""
    try:
        # Get the distant __init__.py and read its version as it done in setup.py
        response = urlrequest.urlopen("https://github.com/NMRTeamTBI/MultiNMRFit/raw/master/multinmrfit/__init__.py")
        data = response.read()
        txt = data.decode('utf-8').rstrip()
        lastversion = re.findall(r"^__version__ = ['\"]([^'\"]*)['\"]", txt, re.M)[0]
        if lastversion != multinmrfit.__version__:
            messagebox.showwarning('Version {} available'.format(lastversion), f'A new version ({lastversion}) is available!\n\nYou can update MultiNMRFit with:\n\n   python -m pip install --upgrade git+https://github.com/NMRTeamTBI/MultiNMRFit\n\nCheck the documentation for more information.')
    except :
        pass  # silently ignore everything that just happened

class App:

    def __init__(self, user_input, *args, **kwargs):
        APP_NAME = f"Multinmrfit Interface (v{multinmrfit.__version__})"
        
        super().__init__(*args, **kwargs)
        self.master = tk.Tk()
        self.master.title(APP_NAME)
        self.master.resizable(False, False)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        threadUpd = threading.Thread(target=check_up_to_date)
        threadUpd.start()

        self.toplevel = None
        if sys.platform == "darwin":
            self.master.bind("<Command-q>", self.on_closing)
            self.master.bind("<Command-w>", self.on_closing)

        # Create Menu     
        menubar = tk.Menu(self.master)
        self.master.config(menu = menubar)
        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Exit", command=self.master.quit)
        helpmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # Add options here if needed
        helpmenu.add_command(label = "MultiNMRFit project", command=openGit)
        helpmenu.add_command(label = "Documentation", command=openDoc)

        # ============ create TkFrames ============
        self.frame_inputs = tk.LabelFrame(self.master,width=250,height=250,text="Inputs",foreground='red')
        self.frame_analysis = tk.LabelFrame(self.master,width=250,height=250,text="Analysis",foreground='red')
        self.frame_output = tk.LabelFrame(self.master,width=250,height=200,text="Outputs",foreground='red')
        self.frame_options = tk.LabelFrame(self.master,width=250,height=200,text="Options",foreground='red')

        self.frame_inputs.grid(row=0,column=0, columnspan=2, padx=3, pady=3)
        self.frame_analysis.grid(row=0,column=2, columnspan=2, padx=3, pady=3)
        self.frame_output.grid(row=1,column=0, columnspan=2, padx=3, pady=3)
        self.frame_options.grid(row=1,column=2, columnspan=2, padx=3, pady=3)

        # ============ create Labels and entries ============
        data_inputs = ['data_path', 'data_folder', 'data_exp_no', 'data_proc_no']
        for i in range(len(data_inputs)):
            data_input_label = tk.Label(self.frame_inputs,text=data_inputs[i].replace("_", " ").capitalize() + ":",foreground='black')
            data_input_label.place(relx=0.1, rely=0.05+i*0.25, anchor="w")

            self.input_var = tk.StringVar() 
            self.input_entry = tk.Entry(self.frame_inputs,textvariable=self.input_var,bg='white',borderwidth=0,foreground='black')
            self.input_entry.place(relx=0.1, rely=0.15+i*0.25,width=200, anchor=tkinter.W)
            user_input[data_inputs[i]]  = self.input_var

        analysis_info = ['analysis_type','reference_spectrum','spectral_limits','threshold']
        for i in range(len(analysis_info)):
            analysis_info_label = tk.Label(self.frame_analysis,text=analysis_info[i].replace("_", " ").capitalize() + ":",foreground='black')
            analysis_info_label.place(relx=0.1, rely=0.05+i*0.25, anchor="w")

            if analysis_info[i] == 'analysis_type':
                self.analysis_info_var = tk.StringVar()
                self.analysis_type_cb = ttk.Combobox(self.frame_analysis,textvariable=self.analysis_info_var, values=['Pseudo2D','1D_Series'], state="readonly")
                self.analysis_type_cb.place(relx=0.1, rely=0.15+i*0.25, anchor=tkinter.W)
                user_input[analysis_info[i]]  = self.analysis_info_var
                self.analysis_type_cb.bind("<<ComboboxSelected>>", self.update_analysis_type)
            else:
                self.analysis_info_var = tk.StringVar()
                analysis_info_entry = tk.Entry(self.frame_analysis,textvariable=self.analysis_info_var,bg='white',borderwidth=0,foreground='black')
                analysis_info_entry.place(relx=0.1, rely=0.15+i*0.25,width=200, anchor=tkinter.W)
                user_input[analysis_info[i]]  = self.analysis_info_var

        outputs = ['output_path','output_folder','output_name']
        for i in range(len(outputs)):
            text_opt = outputs[i].replace("_", " ").capitalize() + ":" if not 'Options' in outputs[i] else outputs[i].replace("_", " ") 
            output_label = tk.Label(self.frame_output,text=text_opt,foreground='black')
            output_label.place(relx=0.1, rely=0.08+i*0.32, anchor="w")

            self.outputs_var = tk.StringVar()
            outputs_entry = tk.Entry(self.frame_output,textvariable=self.outputs_var,bg='white',borderwidth=0,foreground='black')
            outputs_entry.place(relx=0.1, rely=0.2+i*0.32,width=200, anchor=tkinter.W)
            user_input[outputs[i]]  = self.outputs_var

        # # ============ create Buttons ============
        self.load_button = tk.Button(self.master,text=" Load ",command=lambda:nio.load_config_file(self.master,user_input),foreground='black')
        #self.load_button.place(relx=0.1, rely=0.9)
        self.load_button.grid(row=2, column=0, padx=3, pady=5)

        self.save_button = tk.Button(self.master,text=" Save ",command=lambda:self.save_config_file({k: v.get() for k, v in user_input.items()}),foreground='black')
        #self.save_button.place(relx=0.3, rely=0.9)
        self.save_button.grid(row=2, column=1, padx=3, pady=5)

        self.run_button = tk.Button(self.master,text=" Run ",command=lambda:self.App_Run(user_input),foreground='black')
        #self.run_button.place(relx=0.5, rely=0.9)
        self.run_button.grid(row=2, column=2, padx=3, pady=5)

        self.close_button = tk.Button(self.master,text=" Close ",command=lambda:self.on_closing(),foreground='black')
        #self.close_button.place(relx=0.7, rely=0.9)
        self.close_button.grid(row=2, column=3, padx=3, pady=5)

        # # ============ Options ============

        self.input_raws_label = tk.Label(self.frame_options,text='Data row no (* 2D only):',justify=tk.CENTER,foreground='black')
        self.input_raws_label.place(relx=0.05, rely=0.08, anchor="w")

        self.input_raws = tk.StringVar()
        self.input_raws_entry = tk.Entry(self.frame_options,textvariable=self.input_raws,bg='white',fg='black',borderwidth=0,state='disabled' if user_input['analysis_type'] == '1D_Series' else 'normal')
        self.input_raws_entry.place(relx=0.1, rely=0.18, width=200, anchor=tkinter.W)
        user_input['option_data_row_no'] = self.input_raws

        # Use previous fit results as starting parameters
        self.TimeSeries = tk.BooleanVar()
        self.check_box_opt2 = tk.Checkbutton(self.frame_options,text="Use previous fit",variable=self.TimeSeries,foreground='black')
        self.check_box_opt2.place(relx=0.05, rely=0.33, anchor=tkinter.W)
        user_input['option_previous_fit'] = self.TimeSeries

        # if (user_input['analysis_type'] == 'Pseudo2D' or user_input.get('option_previous_fit', False)):
        #     self.check_box_opt2.select()
        # else:
        #     self.check_box_opt2.deselect()
        #self.update_analysis_type(None)
        
        # Use Offset in Fitting
        self.Offset = tk.BooleanVar()
        self.check_box_opt3 = tk.Checkbutton(self.frame_options,text="Offset",variable=self.Offset,foreground='black')
        self.check_box_opt3.place(relx=0.05, rely=0.43, anchor=tkinter.W)
        user_input['option_offset'] = self.Offset

        # # Verbose Log
        self.VerboseLog = tk.BooleanVar()
        self.check_box_opt4 = tk.Checkbutton(self.frame_options,text="Verbose log",variable=self.VerboseLog,foreground='black')
        self.check_box_opt4.place(relx=0.05, rely=0.53, anchor=tkinter.W)
        user_input['option_verbose_log'] = self.VerboseLog

        # # Verbose Log
        self.mergepdf = tk.BooleanVar()
        self.check_box_opt5 = tk.Checkbutton(self.frame_options,text="Merge pdf(s)",variable=self.mergepdf,foreground='black')
        self.check_box_opt5.place(relx=0.05, rely=0.63, anchor=tkinter.W)
        user_input['option_merge_pdf'] = self.mergepdf

        # optimization algorithm
        self.optimizer_label = tk.Label(self.frame_options,text='Optimization algorithm:',justify=tk.CENTER,foreground='black')
        self.optimizer_label.place(relx=0.05, rely=0.78, anchor="w")
        vals = ['L-BFGS-B', 'DE + L-BFGS-B']
        self.optimizer = tk.StringVar()
        self.optimizer.set(vals[0])
        self.optimizer_BFGS = tk.Radiobutton(self.frame_options, variable=self.optimizer, text=vals[0], value=vals[0])
        self.optimizer_BFGS.place(relx=0.05, rely=0.90, anchor=tkinter.W)
        self.optimizer_DE_BFGS = tk.Radiobutton(self.frame_options, variable=self.optimizer, text=vals[1], value=vals[1])
        self.optimizer_DE_BFGS.place(relx=0.55, rely=0.90, anchor=tkinter.W)
        user_input['option_optimizer'] = self.optimizer
        
    def update_analysis_type(self, event):
        if self.analysis_type_cb.get() == "Pseudo2D":
            self.check_box_opt2.select()
        else:
            self.check_box_opt2.deselect()

    def App_Run(self, user_input):
        user_input = nio.check_input_file({k: v.get() for k, v in user_input.items()},self.master)
        nrun.run_analysis(user_input,self)
        self.on_closing()

    def ask_filename(self,config_path, event=0):
        wdw = tk.Tk()
        wdw.withdraw()
        # the input dialog
        file_name = simpledialog.askstring(
            title="Config File Name",
            prompt="Config Input File Name:",
            initialvalue="Inputs_Spec_Fitting"
            )
        if file_name is None:
            wdw.destroy()
            config_file = None
        else:
            config_file = Path(config_path,str(file_name)+'.json')
            wdw.destroy()
        return config_file

    def save_config_file(self,user_input): 
        config_path = Path(user_input['output_path'], user_input['output_folder'])

        try:
            config_path.mkdir(parents=True,exist_ok=True)
        except:
            print("Cannot create output folder.")

        file_name = self.ask_filename(config_path)

        if not 'option_data_row_no' in user_input:
            pass
        else:
            if not user_input['option_data_row_no']:
                del user_input['option_data_row_no']
        if file_name :
            f = open(str(Path(file_name)), "a")
            f.seek(0)
            f.truncate()
            f.write(json.dumps(user_input, indent=4))
            f.close()  

    def activateCheck(self):
        if  self.PartialPseudo2D.get():          #whenever checked
            self.input_entry.config(state='normal')
        else:        #whenever unchecked
            self.input_entry.config(state='disabled')

    def on_closing(self, event=0):
        self.master.destroy()
        exit()

    def start(self):
        self.master.mainloop()

class App_Clustering:
    
    def __init__(self, x_spec, y_spec, peak_picking_threshold, clustering_table, *args, **kwargs):
        self.APP_NAME = f"Peak Picking Visualisation and Clustering (v{multinmrfit.__version__})"
       
        super().__init__(*args, **kwargs)
        self.master = tk.Tk()
        self.peak_picking_threshold = peak_picking_threshold
        self.master.title(self.APP_NAME)
        self.master.resizable(False, False)
        
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.widget = None
        
        self.df_var = tk.StringVar()

        self.toplevel = None
        if sys.platform == "darwin":
            self.master.bind("<Command-q>", self.on_closing)
            self.master.bind("<Command-w>", self.on_closing)

        # # ============ create TkFrames ============
        self.frame_graph = tk.LabelFrame(self.master,width=500,height=500,text="Reference spectrum",foreground='red')
        self.frame_threshold = tk.LabelFrame(self.master,width=500,height=70,text="Threshold",foreground='red')
        self.frame_peak_Table = tk.LabelFrame(self.master,width=640,height=570,text="Clustering information",foreground='red')

        self.frame_graph.grid(row=0,column=0, sticky="nsew", padx=3, pady=5)
        self.frame_threshold.grid(row=1,column=0, padx=3, pady=5)
        # self.frame_peak_Table.grid(row=0,column=2)
        self.frame_peak_Table.grid(row=0, column=1, sticky="nsew", padx=3, pady=5, columnspan=3)

        # # ============ Figure ============
        peak_picking_data = self.peak_picking(x_spec, y_spec, self.peak_picking_threshold)
        colors = self.create_plot(x_spec, y_spec, self.peak_picking_threshold,peak_picking_data)
        self.clustering_information = self.create_table(peak_picking_data,colors) 

        # # ============ Entry ============
        self.threshold_var = tk.StringVar()
        self.threshold_entry = tk.Entry(self.frame_threshold,justify = "center",bg='white',borderwidth=0,foreground='black')
        self.threshold_entry.insert(0, self.peak_picking_threshold)                                  
        self.threshold_entry.place(relx=.5, rely=.3, anchor="c")
        
        # # ============ Buttons ============
        self.refresh_th = tk.Button(self.master,text=" Update Threshold ",command=lambda:self.refresh_ui(x_spec, y_spec, self.threshold_entry.get(),colors),foreground='black')          
        self.refresh_th.grid(row=1, column=1, padx=3, pady=5)

        self.run = tk.Button(self.master,text=" Run Fitting ",command=lambda:self.save_info_clustering(clustering_table),foreground='black')
        self.run.grid(row=1, column=2, padx=3, pady=5)

        self.close_button = tk.Button(self.master,text=" Close ",command=lambda:self.on_closing(),foreground='black')
        self.close_button.grid(row=1, column=3, padx=3, pady=5)

    def peak_picking(self, x_spec_ref, y_spec_ref, threshold):
        peak_picking = nfu.Peak_Picking_1D(
            x_data          =   x_spec_ref, 
            y_data          =   y_spec_ref, 
            threshold       =   threshold,
        )
        peak_picking = nfu.sort_peak_picking_data(peak_picking, 15)        
        return peak_picking

    def create_table(self,peak_picking_data,colors):
        n_peak = len(peak_picking_data)

        clustering_information = {
            'Peak Position'    :   [],
            'Peak Intensity'   :   [],
            'Cluster ID'       :   [],
            'Options'          :   []
        }

        options = ['Roof'] # options
        
        if not n_peak:
            self.th_label = tk.Label(
                self.frame_threshold, 
                text='No peak found, please lower the threshold',
                foreground='red'
            )
            self.th_label.place(relx=0.25, rely=0.7, anchor=tkinter.W)   
        else:
            try:
                self.th_label.destroy()
            except:
                pass

            c = 0 
            for label in clustering_information.keys():
                tk.Label(self.frame_peak_Table, text=label,foreground='black').grid(column=c+1, row=2,padx=2)
                c +=1
                
            for i in range(n_peak):
                peak_label = tk.Label(self.frame_peak_Table, text="Peak "+str(i+1),fg=colors[i])
                peak_label.grid(column=0, row=i+3,pady=5)

                # Clustering
                self.cluster_entry = tk.Entry(self.frame_peak_Table,justify = "center",background='white',foreground='black')
                clustering_information['Cluster ID'].append(self.cluster_entry)
                self.cluster_entry.grid(row=i+3,column=3)

                # Options
                self.options_entry = ttk.Combobox(self.frame_peak_Table, values=options,width=12)
                clustering_information['Options'].append(self.options_entry)
                self.options_entry.grid(row=i+3,column=4)

                # Positions and Intensities
                for col in peak_picking_data.columns:
                    self.entry_c = tk.Entry(
                                            self.frame_peak_Table,
                                            justify = "center",
                                            width=12,
                                            bg='white',
                                            fg='black',
                                            )
                    data = peak_picking_data.iloc[i].loc[col]
                    if col == 'Peak_Position':
                        clustering_information['Peak Position'].append(data)
                        cc = 0
                    if col == 'Peak_Intensity':
                        clustering_information['Peak Intensity'].append(data)
                        cc = 1
                    self.entry_c.insert(0, round(data,3))
                    self.entry_c.grid(column=cc+1,row=i+3)

        return clustering_information

    def save_info_clustering(self, clustering_table):
        clustering_table.Peak_Intensity = self.clustering_information['Peak Intensity']
        clustering_table.Peak_Position = self.clustering_information['Peak Position']
        clustering_table.Options = [i.get() for i in self.clustering_information["Options"]]
        clustering_table.Cluster = [i.get() for i in self.clustering_information["Cluster ID"]]
        clustering_table.Selection = [True if i.get() != '' else False for i in self.clustering_information["Cluster ID"]]
        if not True in clustering_table.Selection.tolist():
            messagebox.showerror("Error", 'No peak selected. Select at least one signal.')
        else:
            self.master.destroy()

    def create_plot(self, x_spec, y_spec, threshold,peak_picking_data):
        
        # remove old widgets
        if self.widget:
            self.widget.destroy()

        n_peak = len(peak_picking_data)

        # Create a list of colors
        colors = []
        for i in range(n_peak):
            colors.append('#%06X' % random.randint(0, 0xFFFFFF))

        fig = plt.Figure(figsize=(6,5), dpi=100)
        ax1 = fig.add_subplot(111)
        ax1.plot(x_spec, y_spec, '-',color='teal')
        for i in range(n_peak):
            ax1.plot(
                peak_picking_data.Peak_Position.iloc[i],
                peak_picking_data.Peak_Intensity.iloc[i],
                c=colors[i],
                ls='none',
                marker='o'
                )
        ax1.axhline(float(threshold),c='r')
        ax1.invert_xaxis()
        ax1.set_xlabel(r'$chemical$ $shift$ $(ppm)$')

        self.graph = FigureCanvasTkAgg(fig, self.frame_graph)
        self.graph_canvas = self.graph.get_tk_widget()
        self.graph_canvas.grid(row=0, column=0)
        return colors

    def refresh_ui(self, x_spec, y_spec, threshold, colors):
        peak_picking = self.peak_picking(x_spec, y_spec, float(threshold))
        colors = self.create_plot(x_spec, y_spec, threshold, peak_picking)
        self.clear_frame()
        self.clustering_information = self.create_table(peak_picking,colors)

    def clear_frame(self):
        for widgets in self.frame_peak_Table.winfo_children():
            widgets.destroy()
        
    def add_frame(self):
        self.test = tk.LabelFrame(self.master,width=500,height=100,text="Test",foreground='red')
        self.test.grid(row=2,column=0, sticky="nsew", padx=3, pady=5)

    def on_closing(self, event=0):
        self.master.destroy()
        exit()

    def start(self):
        self.master.mainloop()

##########
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
        value_label = tk.Label(
                        root,
                        text=progress_bar_label[len(progress_bars)],
                        fg='black',
                        justify=tk.CENTER
)
        value_label.grid(column=0, row=len(len_progresses)*len(progress_bars), columnspan=2)

        pg_bar.grid(column=0, row=len(len_progresses)*len(progress_bars)+1, columnspan=2, padx=10, pady=20)
        progress_bars.append(pg_bar)

    close_button = tk.Button(root, text="Close", fg = "black", command=lambda: progress_bar_exit(root))
    close_button.grid(column = 1, row = len(len_progresses)+5)
    return root, close_button, progress_bars

def progress_bar_exit(root):
    root.destroy()


