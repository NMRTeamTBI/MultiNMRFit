from re import L
import tkinter
import tkinter.messagebox
import pkg_resources
import random

import sys
import json
from pathlib import Path 
import tkinter as tk
from tkinter import simpledialog, ttk, filedialog
from PIL import Image, ImageTk
import logging

# Import math libraries
import pandas as pd
import numpy as np

# Import plot libraries
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import multinmrfit.io as nio
import multinmrfit.run as nrun
import multinmrfit.utils_nmrdata as nfu

logger = logging.getLogger(__name__)
# logger = logging.getLogger()

 
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
        APP_NAME = "Multinmrfit Interface (v2.0)"
        WIDTH = 1200
        HEIGHT = 600
        
        MAIN_COLOR = "#5EA880"
        OPTION_COLOR = "#001933"
        BUTTON_COLOR = "#1c4587"

        ENTRY_COLOR = "#3a8eba"
        MAIN_HOVER = "#3a8eba"
        FRAME_COLOR = '#708090'

        super().__init__(*args, **kwargs)
        master = tk.Tk()
        self.master = master
        master.title(APP_NAME)
        master.geometry(str(WIDTH) + "x" + str(HEIGHT))
        master.minsize(WIDTH, HEIGHT)
        master.configure(bg='#2F4F4F')
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # self.configure("TCombobox", fieldbackground= "orange", background= "white")
        self.toplevel = None
        if sys.platform == "darwin":
            master.bind("<Command-q>", self.on_closing)
            master.bind("<Command-w>", self.on_closing)
        
        # ============ create CTkFrames ============
        self.frame_inputs = tk.Frame(master,
                                    width=250,
                                    height=HEIGHT-250,
                                    bg=FRAME_COLOR
                                    )
        self.frame_inputs.place(relx=0.02, rely=0.1, anchor=tkinter.NW)

        self.frame_analysis = tk.Frame(master,
                                    width=250,
                                    height=HEIGHT-250,
                                    bg=FRAME_COLOR
                                    )
        self.frame_analysis.place(relx=0.25, rely=0.1, anchor=tkinter.NW)

        self.frame_output = tk.Frame(master,
                                    width=250,
                                    height=HEIGHT-250,
                                    bg=FRAME_COLOR
                                    )
        self.frame_output.place(relx=0.48, rely=0.1, anchor=tkinter.NW)

        self.frame_options = tk.Frame(master,
                                                width=330,
                                                height=HEIGHT-250,
                                                bg=FRAME_COLOR
                                                # fg_color=("white", "gray18")
                                                )
        self.frame_options.place(relx=0.71, rely=0.1, anchor=tkinter.NW)

        # self.frame_options_1DSeries = tk.Frame(master,
        #                                         width=250,
        #                                         height=150,
        #                                         bg=FRAME_COLOR
        #                                         # fg_color=("white", "gray18")
        #                                         )
        # self.frame_options_1DSeries.place(relx=0.71, rely=0.4, anchor=tkinter.NW)

         # ============ create CTkFrames ============
        # Set bottom picture
        path_image = pkg_resources.resource_filename('multinmrfit', 'data/')
        img_network = Image.open(str(Path(path_image, 'network.png')))
        self.img_network = ImageTk.PhotoImage(img_network.resize((800, 200)),Image.ANTIALIAS) 
        self.img_network_label = tkinter.Label(master, image = self.img_network)
        self.img_network_label.place(relx = 0.02, rely = 0.7)

        # ============ create Labels and entries ============
        title = ['Inputs','Analysis','Outputs', 'Options']
        for i in range(len(title)):
            tk.Label(
                master,
                text=title[i].replace("_", " ").capitalize() ,
                font=("Helvetica", 18, 'normal'),
                bg=MAIN_HOVER,
                fg='white',
                width=10,
                borderwidth=0,
                justify=tk.CENTER
            ).place(relx=0.02+i*0.23, rely=0.1, anchor=tkinter.W)


        inputs=['data_path','data_folder','data_exp_no','data_proc_no']
        for i in range(len(inputs)):
            tk.Label(
                self.frame_inputs,
                width=10,
                text=inputs[i].replace("_", " ").capitalize(),
                font=("Helvetica", 14, 'normal'),
                borderwidth=0,
                fg='white',
                bg=FRAME_COLOR,
                justify=tk.CENTER
            ).place(relx=0.5, rely=0.1+i*0.2, anchor="center")

            self.input_var = tk.StringVar() 
            self.input_entry = tk.Entry(
                                    self.frame_inputs,
                                    textvariable=self.input_var,
                                    bg='white',
                                    fg='black',
                                    borderwidth=0,
                                    )
            self.input_entry.place(relx=0.1, rely=0.2+i*0.2, width=200, anchor=tkinter.W)
            user_input[inputs[i]]  = self.input_var


        analysis_info = ['analysis_type','reference_spectrum','spectral_limits','threshold']

        style= ttk.Style()
        style.theme_use('clam')
        # style.configure("TCombobox", fieldbackground= "blue", background= "white")

        for i in range(len(analysis_info)):
            tk.Label(
                self.frame_analysis,
                text=analysis_info[i].replace("_", " ").capitalize(),
                font=("Helvetica", 14, 'normal'),
                width=20,
                borderwidth=0,
                fg='white',
                bg=FRAME_COLOR,
                #justify=tk.CENTER
            ).place(relx=0.5, rely=0.1+i*0.2, anchor="center")

            if analysis_info[i] == 'analysis_type':
                self.analysis_info_var = tk.StringVar()
                ttk.Combobox(
                            self.frame_analysis,
                            textvariable=self.analysis_info_var, 
                            values=['Pseudo2D','1D_Series'], 
                            state="readonly",
                            # bg='white',
                            # fg='black',
                ).place(relx=0.1, rely=0.2+i*0.2, width=200, anchor=tkinter.W)
                user_input[analysis_info[i]]  = self.analysis_info_var

            else:
                self.analysis_info_var = tk.StringVar()
                analysis_info_entry = tk.Entry(
                                        self.frame_analysis,
                                        textvariable=self.analysis_info_var,   
                                        bg='white',
                                        fg='black',
                                        borderwidth=0,
                                        )
                analysis_info_entry.place(relx=0.1, rely=0.2+i*0.2, width=200, anchor=tkinter.W)
                user_input[analysis_info[i]]  = self.analysis_info_var


        outputs = ['output_path','output_folder','output_name']
        for i in range(len(outputs)):
            tk.Label(
                self.frame_output,
                text=outputs[i].replace("_", " ").capitalize() if not 'Options' in outputs[i] else outputs[i].replace("_", " ") ,
                font=("Helvetica", 14, 'normal'),
                width=20,
                borderwidth=0,
                fg='white',
                bg=FRAME_COLOR,
                #justify=tk.CENTER
            ).place(relx=0.5, rely=0.1+i*0.2, anchor="center")

            self.outputs_var = tk.StringVar()
            outputs_entry = tk.Entry(
                                self.frame_output,
                                textvariable=self.outputs_var,
                                bg='white',
                                fg='black',
                                borderwidth=0
                                )
            outputs_entry.place(relx=0.1, rely=0.2+i*0.2, width=200, anchor=tkinter.W)
            user_input[outputs[i]]  = self.outputs_var


        # ============ create Buttons ============
        self.load_button = tk.Button(master,
                                            text=" Load ",
                                            highlightbackground =FRAME_COLOR,
                                            fg='black',
                                            borderwidth=0,
                                            font=("Helvetica", 20, 'normal'),
                                            command=lambda:nio.load_config_file(self.master,user_input))
        self.load_button.place(relx=0.74, rely=0.70,width=80,height=30)

        self.save_button = tk.Button(master,
                                            text=" Save ",
                                            highlightbackground =FRAME_COLOR,
                                            fg='black',
                                            borderwidth=0,
                                            font=("Helvetica", 20, 'normal'),
                                            command=lambda:self.save_config_file({k: v.get() for k, v in user_input.items()}))
        self.save_button.place(relx=0.81, rely=0.70,width=80,height=30)

        self.run_button = tk.Button(master,
                                            text=" Run ",
                                            highlightbackground =FRAME_COLOR,
                                            fg='black',
                                            borderwidth=0,
                                            font=("Helvetica", 20, 'normal'),
                                            command=lambda:self.App_Run(user_input))
        self.run_button.place(relx=0.74, rely=0.80,width=80,height=30)

        self.close_button = tk.Button(master,
                                            text=" Close ",
                                            highlightbackground =FRAME_COLOR,
                                            fg='black',
                                            borderwidth=0,
                                            font=("Helvetica", 20, 'normal'),
                                            command=lambda:self.on_closing())
        self.close_button.place(relx=0.81, rely=0.80,width=80,height=30)

        # # ============ Options ============
        # raw ids for Pseudo2S
        self.PartialPseudo2D = tk.BooleanVar()
        self.check_box_opt1 = tk.Checkbutton(
                                        self.frame_options,
                                        text='Data row no (* partial analysis of Pseudo 2D)',
                                        variable=self.PartialPseudo2D,
                                        width=20,
                                        font=("Helvetica", 14, 'normal'),
                                        borderwidth=0,
                                        fg='white',
                                        bg=FRAME_COLOR,
                                        justify=tk.CENTER,
                                        command=self.activateCheck
             )
        self.check_box_opt1.place(relx=0.05, rely=0.1, width=310, anchor=tkinter.W)

        self.input_raws = tk.StringVar()
        self.input_entry = tk.Entry(
                            self.frame_options,
                            textvariable=self.input_raws,
                            bg='white',
                            fg='black',
                            borderwidth=0,
                            state='disabled' if user_input['analysis_type'] == '1D_Series' else 'normal'
                            )
        self.input_entry.place(relx=0.1, rely=0.2, width=200, anchor=tkinter.W)
        user_input['option_data_row_no'] = self.input_raws

        # # if user_input['analysis_type'] == '1D_Series':
        # #     self.input_entry.config(state='disabled')
        # #     self.check_box_opt1.config(state='disabled')

        # Use previous Fit dor starting parameters
        self.TimeSeries = tk.BooleanVar()
        self.check_box_opt2 = tk.Checkbutton(
                                self.frame_options,
                                text="Use previous fit (* 1D only)",
                                font=("Helvetica", 14, 'normal'),
                                variable=self.TimeSeries,
                                highlightthickness=0,
                                bd=0,
                                bg=FRAME_COLOR,
                                # state='disabled'
                                )
        self.check_box_opt2.place(relx=0.05, rely=0.3, anchor=tkinter.W)
        user_input['option_previous_fit'] = self.TimeSeries

        # Use Offset in Fitting
        self.Offset = tk.BooleanVar()
        self.check_box_opt3 = tk.Checkbutton(
                                self.frame_options,
                                text="Offset",
                                font=("Helvetica", 14, 'normal'),
                                variable=self.Offset,
                                highlightthickness=0,
                                bd=0,
                                bg=FRAME_COLOR
                                )
        self.check_box_opt3.place(relx=0.05, rely=0.4, anchor=tkinter.W)
        user_input['option_offset'] = self.Offset

        # # Verbose Log
        self.VerboseLog = tk.BooleanVar()
        self.check_box_opt4 = tk.Checkbutton(
                                self.frame_options,
                                text="Verbose log",
                                font=("Helvetica", 14, 'normal'),
                                variable=self.VerboseLog,
                                highlightthickness=0,
                                bd=0,
                                bg=FRAME_COLOR
                                )
        self.check_box_opt4.place(relx=0.05, rely=0.5, anchor=tkinter.W)
        user_input['option_verbose_log'] = self.VerboseLog


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
        
        MAIN_COLOR = "#5EA880"
        self.ENTRY_COLOR = "#3c78d8"
        OPTION_COLOR = "#001933"
        BUTTON_COLOR = "#1c4587"
        self.MAIN_HOVER = "#3a8eba"

        self.FRAME_COLOR = '#708090'

        super().__init__(*args, **kwargs)
        master = tk.Tk()
        self.master = master
    
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
        peak_picking_data = self.peak_picking(x_spec, y_spec, peak_picking_threshold)
        colors = self.create_plot(x_spec, y_spec, peak_picking_threshold,peak_picking_data)
        clustering_information = self.create_table(peak_picking_data,colors) 

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
        self.threshold_entry.insert(0, peak_picking_threshold)                                  
        self.threshold_entry.place(relx=0.4, rely=0.2, width=200, anchor=tkinter.W)

        # ============ Buttons ============
        self.refresh_th = tk.Button(master,
                                    text=" Refresh & Close ",
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
                            command=lambda:self.save_info_clustering(clustering_information, clustering_table)
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

        if not n_peak:
            th_label = tk.Label(
                self.frame_threshold, 
                text='No peak found, please lower the threshold',
                font=("Helvetica", 18, 'bold'),
                borderwidth=0,
                fg='white',
                bg=self.FRAME_COLOR,
            )
            th_label.place(relx=0.25, rely=0.8, anchor=tkinter.W)   
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
                    #font=("Helvetica", 14, 'bold')
                ).grid(column=c+1, row=2,padx=2)
                c +=1
                
            for i in range(n_peak):
                peak_label = tk.Label(
                    self.frame_peak_Table, 
                    text="Peak "+str(i+1),
                    borderwidth=0,
                    # fg='white',
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

    def save_info_clustering(self, clustering_information, clustering_table):

        clustering_table.Peak_Intensity = clustering_information['Peak Intensity']
        clustering_table.Peak_Position = clustering_information['Peak Position']
        clustering_table.Options = [i.get() for i in clustering_information["Options"]]
        clustering_table.Cluster = [i.get() for i in clustering_information["Cluster ID"]]
        clustering_table.Selection = [True if i.get() != '' else False for i in clustering_information["Cluster ID"]]
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
        self.create_table(peak_picking,colors)

    def clear_frame(self):
        for widgets in self.frame_peak_Table.winfo_children():
            widgets.destroy()
        
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


