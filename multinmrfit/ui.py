from re import L
import tkinter
import tkinter.messagebox
import random

import sys
import json
from pathlib import Path 
import tkinter as tk
from tkinter import simpledialog, ttk, filedialog
import logging

# Import plot libraries
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import multinmrfit
import multinmrfit.io as nio
import multinmrfit.run as nrun
import multinmrfit.utils_nmrdata as nfu

logger = logging.getLogger(__name__)

class App_Error:
    def __init__(self, message, *args, **kwargs):
        APP_NAME = "Error"
        WIDTH = 500
        HEIGHT = 100

        super().__init__(*args, **kwargs)
        master = tk.Tk()
        self.master = master
        master.title(APP_NAME)
        master.geometry(str(WIDTH) + "x" + str(HEIGHT))
        master.minsize(WIDTH, HEIGHT)
        master.configure(bg='#2F4F4F')
        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        master.toplevel = None
        self.label = tk.Label(
                            master, 
                            text=message, 
                            width= WIDTH,
                            height=HEIGHT,
                            bg='#2F4F4F',
                            fg='white'
                            )
        self.label.pack()
        # self.configure("TCombobox", fieldbackground= "orange", background= "white")
        self.toplevel = None
        if sys.platform == "darwin":
            master.bind("<Command-q>", self.on_closing)
            master.bind("<Command-w>", self.on_closing)

    def on_closing(self, event=0):
        self.master.destroy()

    def start(self):
        self.master.mainloop()

class App:

    def __init__(self, user_input, *args, **kwargs):
        APP_NAME = f"Multinmrfit Interface (v{multinmrfit.__version__})"
        WIDTH = 500
        HEIGHT = 520
        
        super().__init__(*args, **kwargs)
        master = tk.Tk()
        self.master = master
        master.title(APP_NAME)
        master.geometry(str(WIDTH) + "x" + str(HEIGHT))
        master.minsize(WIDTH, HEIGHT)
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.toplevel = None
        if sys.platform == "darwin":
            master.bind("<Command-q>", self.on_closing)
            master.bind("<Command-w>", self.on_closing)

        #Create Menu     
        menubar = tk.Menu(master)
        master.config(menu = menubar)
        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Exit", command=master.quit)
        helpmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=helpmenu)

        # Add options here if needed
    
        # helpmenu.add_command(label = "IsoCor project", command=openGit)
        # helpmenu.add_command(label = "Documentation", command=openDoc)
        # ============ create CTkFrames ============


        self.frame_inputs = tk.LabelFrame(master,width=250,height=250,text="Inputs",foreground='red')
        self.frame_analysis = tk.LabelFrame(master,width=250,height=250,text="Analysis",foreground='red')
        self.frame_output = tk.LabelFrame(master,width=250,height=200,text="Outputs",foreground='red')
        self.frame_options = tk.LabelFrame(master,width=250,height=200,text="Options",foreground='red')

        self.frame_inputs.grid(row=0,column=1)
        self.frame_analysis.grid(row=0,column=2)
        self.frame_output.grid(row=1,column=1)
        self.frame_options.grid(row=1,column=2)

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
        self.load_button = tk.Button(master,text=" Load ",command=lambda:nio.load_config_file(self.master,user_input),foreground='black')
        self.load_button.place(relx=0.1, rely=0.9)

        self.save_button = tk.Button(master,text=" Save ",command=lambda:self.save_config_file({k: v.get() for k, v in user_input.items()}),foreground='black')
        self.save_button.place(relx=0.3, rely=0.9)

        self.run_button = tk.Button(master,text=" Run ",command=lambda:self.App_Run(user_input),foreground='black')
        self.run_button.place(relx=0.5, rely=0.9)

        self.close_button = tk.Button(master,text=" Close ",command=lambda:self.on_closing(),foreground='black')
        self.close_button.place(relx=0.7, rely=0.9)

        # # ============ Options ============

        self.input_raws_label = tk.Label(self.frame_options,text='Data row no (* 2D only):',justify=tk.CENTER,foreground='black')
        self.input_raws_label.place(relx=0.05, rely=0.08, anchor="w")

        self.input_raws = tk.StringVar()
        self.input_raws_entry = tk.Entry(self.frame_options,textvariable=self.input_raws,bg='white',fg='black',borderwidth=0,state='disabled' if user_input['analysis_type'] == '1D_Series' else 'normal')
        self.input_raws_entry.place(relx=0.1, rely=0.2, width=200, anchor=tkinter.W)
        user_input['option_data_row_no'] = self.input_raws

        # Use previous fit results as starting parameters
        self.TimeSeries = tk.BooleanVar()
        self.check_box_opt2 = tk.Checkbutton(self.frame_options,text="Use previous fit",variable=self.TimeSeries)
        self.check_box_opt2.place(relx=0.05, rely=0.37, anchor=tkinter.W)
        user_input['option_previous_fit'] = self.TimeSeries

        # if (user_input['analysis_type'] == 'Pseudo2D' or user_input.get('option_previous_fit', False)):
        #     self.check_box_opt2.select()
        # else:
        #     self.check_box_opt2.deselect()
        #self.update_analysis_type(None)
        
        # Use Offset in Fitting
        self.Offset = tk.BooleanVar()
        self.check_box_opt3 = tk.Checkbutton(self.frame_options,text="Offset",variable=self.Offset)
        self.check_box_opt3.place(relx=0.05, rely=0.52, anchor=tkinter.W)
        user_input['option_offset'] = self.Offset

        # # Verbose Log
        self.VerboseLog = tk.BooleanVar()
        self.check_box_opt4 = tk.Checkbutton(self.frame_options,text="Verbose log",variable=self.VerboseLog)
        self.check_box_opt4.place(relx=0.05, rely=0.67, anchor=tkinter.W)
        user_input['option_verbose_log'] = self.VerboseLog

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
            initialvalue="Inputs_Spec_Fitting")
        if file_name is None:
            wdw.destroy()
            config_file = None
        else:
            config_file = Path(config_path,str(file_name)+'.json')
            wdw.destroy()
        return config_file

    def save_config_file(self,user_input): 
        config_path = Path(user_input['output_path'], user_input['output_folder'])
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
        self.APP_NAME = "Peak Picking Visualisation and Clustering"
        self.WIDTH = 1200
        self.HEIGHT = 600
        
        self.ENTRY_COLOR = "#3c78d8"
        self.MAIN_HOVER = "#3a8eba"
        self.FRAME_COLOR = '#708090'

        super().__init__(*args, **kwargs)
        master = tk.Tk()
        self.master = master
        self.peak_picking_threshold = peak_picking_threshold
        master.title(self.APP_NAME)
        master.geometry(str(self.WIDTH) + "x" + str(self.HEIGHT))
        master.minsize(self.WIDTH, self.HEIGHT)
        master.configure(bg='#2F4F4F')

        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.widget = None
        
        self.df_var = tk.StringVar()

        # self.configure("TCombobox", fieldbackground= "orange", background= "white")
        self.toplevel = None
        if sys.platform == "darwin":
            master.bind("<Command-q>", self.on_closing)
            master.bind("<Command-w>", self.on_closing)
        # # ============ create CTkFrames ============
        self.frame_graph = tk.Frame(master,
                                    width=500,
                                    height=self.HEIGHT-150,
                                    bg=self.FRAME_COLOR
                                    )
        self.frame_graph.place(relx=0.02, rely=0.03, anchor=tkinter.NW)

        self.frame_threshold = tk.Frame(master,
                                    width=500,
                                    height=self.HEIGHT-520,
                                    bg=self.FRAME_COLOR
                                    )
        self.frame_threshold.place(relx=0.02, rely=0.82, anchor=tkinter.NW)


        self.frame_peak_Table = tk.Frame(master,
                                    width=640,
                                    height=self.HEIGHT-50,
                                    bg=self.FRAME_COLOR
                                    )
        self.frame_peak_Table.place(relx=0.47, rely=0.03, anchor=tkinter.NW)

        # ============ Figure ============
        peak_picking_data = self.peak_picking(x_spec, y_spec, self.peak_picking_threshold)
        colors = self.create_plot(x_spec, y_spec, self.peak_picking_threshold,peak_picking_data)
        self.clustering_information = self.create_table(peak_picking_data,colors) 

        # ============ Labels ============
        tk.Label(
            self.frame_threshold,
            text='Threshold',
            width=10,
            borderwidth=0,
            fg='white',
            bg=self.MAIN_HOVER,
            font=("Helvetica", 18, 'normal'),
            justify=tk.CENTER
        ).place(relx=0.02, rely=0.2, anchor=tkinter.W)

        # ============ Entry ============
        # self.threshold_var = tk.StringVar()
        self.threshold_entry = tk.Entry(
                                    self.frame_threshold,
                                    justify = "center",
                                    width=12,
                                    bg='white',
                                    fg='black',
                                    borderwidth=0,
                                    )
        self.threshold_entry.insert(0, self.peak_picking_threshold)                                  
        self.threshold_entry.place(relx=0.4, rely=0.2, width=200, anchor=tkinter.W)

        # ============ Buttons ============
        self.refresh_th = tk.Button(master,
                                    text=" Update Threshold ",
                                    highlightbackground = self.FRAME_COLOR,
                                    fg='black',
                                    borderwidth=0,
                                    font=("Helvetica", 20, 'normal'),
                                    command=lambda:self.refresh_ui(x_spec, y_spec, self.threshold_entry.get(),colors)
                                    )
          
        self.refresh_th.place(relx=0.54, rely=0.85,width=180,height=50)

        self.run = tk.Button(master,
                            text=" Run Fitting ",
                            highlightbackground = self.FRAME_COLOR,
                            fg='black',
                            borderwidth=0,
                            font=("Helvetica", 20, 'normal'),
                            command=lambda:self.save_info_clustering(clustering_table)
                            )
        self.run.place(relx=0.71, rely=0.85,width=180,height=50)

        self.close_button = tk.Button(master,
                            text=" Close ",
                            highlightbackground = self.FRAME_COLOR,
                            fg='black',
                            borderwidth=0,
                            font=("Helvetica", 20, 'normal'),
                            command=lambda:self.on_closing())
        self.close_button.place(relx=0.88, rely=0.85,width=80,height=50)

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
        print(n_peak)
        if not n_peak:
            self.th_label = tk.Label(
                self.frame_threshold, 
                text='No peak found, please lower the threshold',
                font=("Helvetica", 18, 'bold'),
                borderwidth=0,
                fg='white',
                bg=self.FRAME_COLOR,
            )
            self.th_label.place(relx=0.25, rely=0.8, anchor=tkinter.W)   
        else:
            if len(self.frame_threshold.winfo_children()) >2 :
                self.frame_threshold.winfo_children()[2].destroy()

            tk.Label(
                self.frame_peak_Table,
                text='Clutering',
                width=10,
                borderwidth=0,
                fg='white',
                bg=self.MAIN_HOVER,
                font=("Helvetica", 18, 'normal'),
                justify=tk.CENTER
            ).grid(column=0, row=0)


            c = 0 
            for label in clustering_information.keys():
                tk.Label(
                    self.frame_peak_Table, 
                    text=label, 
                    borderwidth=0,
                    fg='white',
                    bg=self.FRAME_COLOR,
                    width=10
                ).grid(column=c+1, row=2,padx=2)
                c +=1
                
            for i in range(n_peak):
                peak_label = tk.Label(
                    self.frame_peak_Table, 
                    text="Peak "+str(i+1),
                    borderwidth=0,
                    bg=self.FRAME_COLOR,
                    fg=colors[i]
                    )
                peak_label.grid(column=0, row=i+3,pady=5)

                # Clustering
                self.cluster_entry = tk.Entry(
                                            self.frame_peak_Table,
                                            justify = "center",
                                            width=12,
                                            bg='white',
                                            fg='black',
                                            borderwidth=0,
                                            )
                clustering_information['Cluster ID'].append(self.cluster_entry)
                self.cluster_entry.grid(row=i+3,column=3)

                # Options
                self.options_entry = ttk.Combobox(
                                            self.frame_peak_Table, 
                                            values=options,
                                            width=12
                                            )
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
                                            borderwidth=0,
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
        ax1.set_xlabel(r'$^1H$ $(ppm)$')

        self.graph = FigureCanvasTkAgg(fig, self.frame_graph)
        self.graph_canvas = self.graph.get_tk_widget()
        self.graph_canvas.place(relx=0.0,rely=0.0,width=500,height=self.HEIGHT-150)

        return colors

    def refresh_ui(self, x_spec, y_spec, threshold, colors):
        peak_picking = self.peak_picking(x_spec, y_spec, float(threshold))
        colors = self.create_plot(x_spec, y_spec, threshold, peak_picking)
        self.clear_frame()
        self.clustering_information = self.create_table(peak_picking,colors)

    def clear_frame(self):
        for widgets in self.frame_peak_Table.winfo_children():
            widgets.destroy()
        # self.frame_threshold.winfo_children()[3].destroy()

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
    root.configure(bg='#2F4F4F')
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
        value_label = tk.Label(
                        root,
                        text=progress_bar_label[len(progress_bars)],
                        width=10,
                        borderwidth=0,
                        fg='white',
                        bg='#2F4F4F',
                        font=("Helvetica", 18, 'normal'),
                        justify=tk.CENTER
)
        value_label.grid(column=0, row=len(len_progresses)*len(progress_bars), columnspan=2)

        pg_bar.grid(column=0, row=len(len_progresses)*len(progress_bars)+1, columnspan=2, padx=10, pady=20)
        progress_bars.append(pg_bar)

    close_button = tk.Button(
        root, 
        text="Close", 
        fg = "black", 
        bg = '#2F4F4F',
        font=("Helvetica", 20),        
        command=lambda: progress_bar_exit(root)
    )
    close_button.grid(column = 1, row = len(len_progresses)+5)
    return root, close_button, progress_bars

def progress_bar_exit(root):
    root.destroy()


