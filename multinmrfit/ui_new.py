import tkinter
import tkinter.messagebox
import customtkinter
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
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import multinmrfit.io as nio
import multinmrfit.run as nrun
import multinmrfit.fitting as nff
import multinmrfit.utils_nmrdata as nfu

logger = logging.getLogger(__name__)
# logger = logging.getLogger()

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

 

class App_Error(customtkinter.CTk):
    APP_NAME = "Error"
    WIDTH = 500
    HEIGHT = 100
    def __init__(root, message, *args, **kwargs):
        super().__init__(*args, **kwargs)
        root.title(App_Error.APP_NAME)
        root.geometry(str(App_Error.WIDTH) + "x" + str(App_Error.HEIGHT))
        root.minsize(App_Error.WIDTH, App_Error.HEIGHT)
        root.protocol("WM_DELETE_WINDOW", root.on_closing)
        root.toplevel = None
        root.label = customtkinter.CTkLabel(
                            root, 
                            text=message, 
                            width= App_Error.WIDTH,
                            height=App_Error.HEIGHT,
                            )
        root.label.pack()
    def on_closing(root, event=0):
            root.destroy()
    def start(root):
            root.mainloop()

class App(customtkinter.CTk):

    APP_NAME = "Multinmrfit Interface (v2.0)"
    WIDTH = 1200
    HEIGHT = 600
    
    MAIN_COLOR = "#5EA880"
    ENTRY_COLOR = "#3c78d8"
    OPTION_COLOR = "#001933"
    BUTTON_COLOR = "#1c4587"
    MAIN_HOVER = "#458577"

    def __init__(self, user_input, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title(App.APP_NAME)
        self.geometry(str(App.WIDTH) + "x" + str(App.HEIGHT))
        self.minsize(App.WIDTH, App.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # self.configure("TCombobox", fieldbackground= "orange", background= "white")
        self.toplevel = None
        if sys.platform == "darwin":
            self.bind("<Command-q>", self.on_closing)
            self.bind("<Command-w>", self.on_closing)
            self.createcommand('tk::mac::Quit', self.on_closing)
        

        # ============ create CTkFrames ============
        self.frame_inputs = customtkinter.CTkFrame(master=self,
                                                 width=250,
                                                 height=App.HEIGHT-250,
                                                 corner_radius=10)
        self.frame_inputs.place(relx=0.02, rely=0.1, anchor=tkinter.NW)

        self.frame_analysis = customtkinter.CTkFrame(master=self,
                                                  width=250,
                                                  height=App.HEIGHT-250,
                                                  corner_radius=10)
        self.frame_analysis.place(relx=0.25, rely=0.1, anchor=tkinter.NW)

        self.frame_output = customtkinter.CTkFrame(master=self,
                                                  width=250,
                                                  height=App.HEIGHT-250,
                                                  corner_radius=10)
        self.frame_output.place(relx=0.48, rely=0.1, anchor=tkinter.NW)

        self.frame_options_Pseudo2D = customtkinter.CTkFrame(master=self,
                                                  width=250,
                                                  height=150,
                                                  corner_radius=10,
                                                  fg_color=("white", "gray18"))
        self.frame_options_Pseudo2D.place(relx=0.71, rely=0.1, anchor=tkinter.NW)

        self.frame_options_1DSeries = customtkinter.CTkFrame(master=self,
                                                  width=250,
                                                  height=150,
                                                  corner_radius=10,
                                                  fg_color=("white", "gray18"))
        self.frame_options_1DSeries.place(relx=0.71, rely=0.4, anchor=tkinter.NW)

         # ============ create CTkFrames ============
        # Set bottom picture
        path_image = Path('../../../git/MultiNMRFit/multinmrfit/data')
        img_network = Image.open(str(Path(path_image, 'network.png')))
        self.img_network = ImageTk.PhotoImage(img_network.resize((800, 200)),Image.ANTIALIAS) 
        self.img_network_label = tkinter.Label(master=self, image = self.img_network)
        self.img_network_label.place(relx = 0.02, rely = 0.7)


        # ============ create Labels and entries ============
        title = ['Inputs','Analysis','Outputs']
        for i in range(len(title)):
            customtkinter.CTkLabel(
                self,
                text=title[i].replace("_", " ").capitalize() ,
                corner_radius=8,
                width=150,
                borderwidth=0,
                fg_color=App.MAIN_COLOR
                #justify=tk.CENTER
            ).place(relx=0.02+i*0.23, rely=0.1, anchor=tkinter.W)


        inputs=['data_path','data_folder','data_exp_no','data_proc_no']
        for i in range(len(inputs)):
            customtkinter.CTkLabel(
                                self.frame_inputs,
                                width=150,
                                text=inputs[i].replace("_", " ").capitalize()  ,
                                corner_radius=8,
                                borderwidth=0,
                                fg_color=App.ENTRY_COLOR
                #justify=tk.CENTER
            ).place(relx=0.2, rely=0.1+i*0.2, anchor=tkinter.W)

            self.input_var = tk.StringVar() 
            self.input_entry = customtkinter.CTkEntry(
                                                self.frame_inputs,
                                                textvariable=self.input_var,
                                                corner_radius=8)
            self.input_entry.place(relx=0.1, rely=0.2+i*0.2, width=200, anchor=tkinter.W)
            user_input[inputs[i]]  = self.input_var


            # user_input[inputs[i]] = self.create_entry(self.frame_inputs,inputs[i], 0.25, 0.1+i*0.2,"#5743bb")

        analysis_info = ['analysis_type','reference_spectrum','spectral_limits','threshold']
        for i in range(len(analysis_info)):
            customtkinter.CTkLabel(
                self.frame_analysis,
                text=analysis_info[i].replace("_", " ").capitalize(),
                corner_radius=8,
                width=150,
                borderwidth=0,
                fg_color=App.ENTRY_COLOR
                #justify=tk.CENTER
            ).place(relx=0.2, rely=0.1+i*0.2, anchor=tkinter.W)

            if analysis_info[i] == 'analysis_type':
                self.analysis_info_var = tk.StringVar()
                ttk.Combobox(
                    self.frame_analysis,
                    textvariable=self.analysis_info_var, 
                    values=['1D','Pseudo2D','1D_Series'], 
                    state="readonly"
                ).place(relx=0.1, rely=0.2+i*0.2, width=200, anchor=tkinter.W)
                user_input[analysis_info[i]]  = self.analysis_info_var

            else:
                self.analysis_info_var = tk.StringVar()
                analysis_info_entry = customtkinter.CTkEntry(
                                                    self.frame_analysis,
                                                    textvariable=self.analysis_info_var,
                                                    corner_radius=8)
                analysis_info_entry.place(relx=0.1, rely=0.2+i*0.2, width=200, anchor=tkinter.W)
                user_input[analysis_info[i]]  = self.analysis_info_var


        outputs = ['output_path','output_folder','output_name']
        for i in range(len(outputs)):
            customtkinter.CTkLabel(
                self.frame_output,
                text=outputs[i].replace("_", " ").capitalize() if not 'Options' in outputs[i] else outputs[i].replace("_", " ") ,
                corner_radius=8,
                borderwidth=0,
                width=150,                
                fg_color=App.ENTRY_COLOR
                #justify=tk.CENTER
            ).place(relx=0.2, rely=0.1+i*0.2, anchor=tkinter.W)

            self.outputs_var = tk.StringVar()
            outputs_entry = customtkinter.CTkEntry(
                                                self.frame_output,
                                                textvariable=self.outputs_var,
                                                corner_radius=8)
            outputs_entry.place(relx=0.1, rely=0.2+i*0.2, width=200, anchor=tkinter.W)
            user_input[outputs[i]]  = self.outputs_var


        # ============ create Buttons ============
        self.load_button = customtkinter.CTkButton(master=self,
                                            text=" Load ",
                                            corner_radius=10,
                                            fg_color=App.BUTTON_COLOR,
                                            command=lambda:nio.load_config_file(self,user_input))
        self.load_button.place(relx=0.74, rely=0.70,width=80,height=50)

        self.save_button = customtkinter.CTkButton(master=self,
                                            text=" Save ",
                                            corner_radius=10,
                                            fg_color=App.BUTTON_COLOR,
                                            command=lambda:self.save_config_file({k: v.get() for k, v in user_input.items()}))
        self.save_button.place(relx=0.81, rely=0.70,width=80,height=50)

        self.run_button = customtkinter.CTkButton(master=self,
                                            text=" Run ",
                                            corner_radius=10,
                                            fg_color=App.BUTTON_COLOR,
                                            command=lambda:self.App_Run(user_input))
        self.run_button.place(relx=0.74, rely=0.80,width=80,height=50)

        self.close_button = customtkinter.CTkButton(master=self,
                                            text=" Close ",
                                            corner_radius=10,
                                            fg_color=App.BUTTON_COLOR,
                                            command=lambda:self.on_closing())
        self.close_button.place(relx=0.81, rely=0.80,width=80,height=50)

        # # ============ Options ============
        option_list = []
        customtkinter.CTkLabel(
            self,
            text='Options: Pseudo2D',
            corner_radius=8,
            width=200,
            borderwidth=0,
            fg_color=App.OPTION_COLOR
            #justify=tk.CENTER
        ).place(relx=0.02+3*0.23, rely=0.1, anchor=tkinter.W)

        customtkinter.CTkLabel(
            self,
            text='Options: 1DSeries',
            corner_radius=8,
            width=200,
            borderwidth=0,
            fg_color=App.OPTION_COLOR
            #justify=tk.CENTER
        ).place(relx=0.02+3*0.23, rely=0.4, anchor=tkinter.W)


        self.TimeSeries = tk.IntVar()
        self.check_box_1 = customtkinter.CTkCheckBox(
                                            self.frame_options_1DSeries,
                                            text="Time Series",
                                            variable=self.TimeSeries
                                            )
        self.check_box_1.place(relx=0.25, rely=0.2, anchor=tkinter.W)
        user_input['time_series'] = self.TimeSeries

        customtkinter.CTkLabel(
            self.frame_options_Pseudo2D,
            text='raw ids',
            corner_radius=8,
            width=200,
            borderwidth=0,
            fg_color=App.OPTION_COLOR
            #justify=tk.CENTER
        ).place(relx=0.1, rely=0.25, anchor=tkinter.W)
        
        self.input_raws = tk.StringVar()
        input_entry = customtkinter.CTkEntry(
                                            self.frame_options_Pseudo2D,
                                            textvariable=self.input_raws,
                                            corner_radius=8)
        input_entry.place(relx=0.1, rely=0.47, width=200, anchor=tkinter.W)
        user_input['data_row_no'] = self.input_raws

    def App_Run(self, user_input):
        user_input = nio.check_input_file({k: v.get() for k, v in user_input.items()},self)
        nrun.run_analysis(user_input,self)
        self.destroy()        


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
        if not user_input['rows_pseudo2D']:
            del user_input['rows_pseudo2D']
        if file_name :
            f = open(file_name, "a")
            f.seek(0)
            f.truncate()
            f.write(json.dumps(user_input, indent=4))
            f.close()  

    

    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()

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

# class App_Clustering()

class App_Clustering(customtkinter.CTk):

    APP_NAME = "Peak Picking Visualisation and Clustering"
    WIDTH = 1200
    HEIGHT = 600
    
    MAIN_COLOR = "#5EA880"
    ENTRY_COLOR = "#3c78d8"
    OPTION_COLOR = "#001933"
    BUTTON_COLOR = "#1c4587"
    MAIN_HOVER = "#458577"
    
    def __init__(self, x_spec, y_spec, peak_picking_threshold, clustering_table, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.title(App_Clustering.APP_NAME)
        self.geometry(str(App_Clustering.WIDTH) + "x" + str(App_Clustering.HEIGHT))
        self.minsize(App_Clustering.WIDTH, App_Clustering.HEIGHT)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.widget = None
        
        self.df_var = tk.StringVar()

        # self.configure("TCombobox", fieldbackground= "orange", background= "white")
        self.toplevel = None
        if sys.platform == "darwin":
            self.bind("<Command-q>", self.on_closing)
            self.bind("<Command-w>", self.on_closing)
            self.createcommand('tk::mac::Quit', self.on_closing)
        # ============ create CTkFrames ============
        self.frame_graph = customtkinter.CTkFrame(master=self,
                                                 width=500,
                                                 height=App.HEIGHT-150,
                                                 corner_radius=10)
        self.frame_graph.place(relx=0.02, rely=0.03, anchor=tkinter.NW)

        self.threshold = customtkinter.CTkFrame(master=self,
                                                 width=500,
                                                 height=App.HEIGHT-520,
                                                 corner_radius=10)
        self.threshold.place(relx=0.02, rely=0.82, anchor=tkinter.NW)

        self.frame_peak_Table = customtkinter.CTkFrame(master=self,
                                                 width=600,
                                                 height=App.HEIGHT-150,
                                                 corner_radius=10)
        self.frame_peak_Table.place(relx=0.47, rely=0.03, anchor=tkinter.NW)

        # ============ Figure ============
        peak_picking_data = self.peak_picking(x_spec, y_spec, peak_picking_threshold)
        self.create_plot(x_spec, y_spec, peak_picking_threshold,peak_picking_data)
        clustering_information = self.create_table(peak_picking_data) 
        

        # ============ Labels ============
        customtkinter.CTkLabel(
            self.threshold,
            text='Threshold',
            corner_radius=8,
            width=150,
            borderwidth=0,
            fg_color=App.ENTRY_COLOR
            #justify=tk.CENTER
        ).place(relx=0.02, rely=0.2, anchor=tkinter.W)


        # ============ Clustering ============

        # ============ Entry ============
        # self.threshold_var = tk.StringVar()
        self.threshold_entry = customtkinter.CTkEntry(
                                            self.threshold,
                                            #textvariable=self.threshold_var,
                                            corner_radius=8)
        self.threshold_entry.insert(0, peak_picking_threshold)                                  
        self.threshold_entry.place(relx=0.4, rely=0.5, width=200, anchor=tkinter.W)

        
        # ============ Buttons ============
        self.refresh_th = customtkinter.CTkButton(master=self,
                                            text=" Refresh & Close ",
                                            corner_radius=10,
                                            fg_color=App.BUTTON_COLOR,
                                            command=lambda:self.refresh_ui(x_spec, y_spec, self.threshold_entry.get())
                                            )
        self.refresh_th.place(relx=0.54, rely=0.90,width=200,height=50)

        self.run = customtkinter.CTkButton(master=self,
                                            text=" Run fitting ",
                                            corner_radius=10,
                                            fg_color=App.BUTTON_COLOR,
                                            command=lambda:self.save_info_clustering(clustering_information, clustering_table)
                                            )
        self.run.place(relx=0.71, rely=0.90,width=200,height=50)

        self.close_button = customtkinter.CTkButton(master=self,
                                            text=" Close ",
                                            corner_radius=10,
                                            fg_color=App.BUTTON_COLOR,
                                            command=lambda:self.on_closing())
        self.close_button.place(relx=0.88, rely=0.90,width=80,height=50)

    def peak_picking(self, x_spec_ref, y_spec_ref, threshold):
        peak_picking = nfu.Peak_Picking_1D(
            x_data          =   x_spec_ref, 
            y_data          =   y_spec_ref, 
            threshold       =   threshold,
        )
        peak_picking = nfu.sort_peak_picking_data(peak_picking, 10)        
        return peak_picking

    def create_table(self,peak_picking_data):
        n_peak = len(peak_picking_data)

        clustering_information = {
            'Peak Position'    :   [],
            'Peak Intensity'   :   [],
            'Cluster ID'       :   [],
            'Options'          :   []
        }

        options = ['Roof'] # options

        customtkinter.CTkLabel(
            self.frame_peak_Table,
            text='Clutering',
            corner_radius=8,
            width=100,
            borderwidth=0,
            fg_color=App.ENTRY_COLOR
            #justify=tk.CENTER
        ).grid(column=0, row=0)
        # ).place(relx=0.02, rely=0.04, anchor=tkinter.W)

        if not n_peak:
            customtkinter.CTkLabel(
                self.refresh_th, 
                text='No peak found, please lower the threshold',
                #font=("Helvetica", 14, 'bold'),
                #fg='#f00'
            ).place(relx=0.02, rely=0.5, anchor=tkinter.W)   
        else:
            c = 0 
            for label in clustering_information.keys():
                customtkinter.CTkLabel(
                    self.frame_peak_Table, 
                    text=label, 
                    #font=("Helvetica", 14, 'bold')
                ).grid(column=c+1, row=2,padx=2)
                c +=1
                
            for i in range(n_peak):
                peak_label = customtkinter.CTkLabel(
                    self.frame_peak_Table, 
                    text="Peak "+str(i+1),
                    #fg=colors[i]
                    )
                peak_label.grid(column=0, row=i+3,pady=5)

                # Clustering
                self.cluster_entry = customtkinter.CTkEntry(
                                                    self.frame_peak_Table,
                                                    justify = "center"
                                                    )
                clustering_information['Cluster ID'].append(self.cluster_entry)
                self.cluster_entry.grid(row=i+3,column=3)

                # Options
                self.options_entry = ttk.Combobox(
                                            self.frame_peak_Table, 
                                            values=options,
                                            width = 10
                                            )
                clustering_information['Options'].append(self.options_entry)
                self.options_entry.grid(row=i+3,column=4)

                # Positions and Intensities
                for col in peak_picking_data.columns:
                    self.entry_c = customtkinter.CTkEntry(
                                                self.frame_peak_Table,
                                                justify = "center"
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
        self.destroy()

                # Cleaning ~~~~~~~~~~~~~~~~~~~~~~~~~~
                # # if int(peak_label.grid_info()["row"]) > n_peak+2:
                # #     print(int(peak_label.grid_info()["row"]))
                # peak_label.grid_remove()
                # # customtkinter.CTkEntry(
                # #     self.frame_peak_Table,
                # #     justify = "center"
                # #     )
#        self.threshold_entry = customtkinter.CTkEntry(
#                                     self.threshold,
#                                     #textvariable=self.threshold_var,
#                                     corner_radius=8)
# self.threshold_entry.insert(0, peak_picking_threshold)                                  
# self.threshold_entry.place(relx=0.4, rely=0.5, width=200, anchor=tkinter.W)
             


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
        self.graph_canvas.place(relx=0.0,rely=0.0,width=500,height=App.HEIGHT-150)

        print(colors)

    def refresh_ui(self, x_spec, y_spec, threshold):
        peak_picking = self.peak_picking(x_spec, y_spec, float(threshold))
        self.create_plot(x_spec, y_spec, threshold, peak_picking)
        self.create_table(peak_picking)

    def on_closing(self, event=0):
        self.destroy()

    def start(self):
        self.mainloop()

def user_clustering_gui(peak_picking_threshold, peak_picking_data, figure, colors, Res):
    # global tk_wdw
    tk_wdw = tk.Tk()
    # tk_wdw.protocol("WM_DELETE_WINDOW", Exit)
    # tk_wdw.title('Peak Picking Visualisation and Validation')

    # graph = FigureCanvasTkAgg(figure, master=tk_wdw)  
    # canvas = graph.get_tk_widget()
    # canvas.grid(row=0, column=0,columnspan = 8,rowspan=1)

    # list_of_options=['Roof'] # options
    
    # user_input = {
    #     'Peak Position'    :   [],
    #     'Peak Intensity'   :   [],
    #     'Cluster ID'       :   [],
    #     'Options'          :   []
    # }

        # npeaks = len(peak_picking_data)
        # if not npeaks:
        #     tk.Label(
        #         tk_wdw, 
        #         text='No peak found, please lower the threshold',
        #         font=("Helvetica", 14, 'bold'),
        #         fg='#f00'
        #     ).grid(column=0, row=3)
        #     tk.Entry(tk_wdw,justify = "center")
        # else:
        #     c = 0 
        #     for label in user_input.keys():
        #         tk.Label(
        #             tk_wdw, 
        #             text=label, 
        #             font=("Helvetica", 14, 'bold')
        #         ).grid(column=c+1, row=2)
        #         c +=1

        #     for i in range(npeaks):
        #         tk.Label(tk_wdw, text="Peak "+str(i+1),fg=colors[i]).grid(column=0, row=i+3)
        #         tk.Entry(tk_wdw,justify = "center")
            
        #         # Clustering
        #         cluster_entry = tk.Entry(tk_wdw,justify = "center")
        #         user_input['Cluster ID'].append(cluster_entry)
        #         cluster_entry.grid(row=i+3,column=3)

        #         options_entry = ttk.Combobox(tk_wdw, values=list_of_options)
        #         user_input['Options'].append(options_entry)
        #         options_entry.grid(row=i+3,column=4)
        #         for col in peak_picking_data.columns:
        #             en_c = tk.Entry(tk_wdw,justify = "center")
        #             data = peak_picking_data.iloc[i].loc[col]
        #             if col == 'Peak_Position':
        #                 user_input['Peak Position'].append(data)
        #                 cc = 0
        #             if col == 'Peak_Intensity':
        #                 user_input['Peak Intensity'].append(data)
        #                 cc = 1
        #             en_c.insert(0, round(data,3))
        #             en_c.grid(column=cc+1,row=i+3)
        
        # tk.Label(
        #     tk_wdw, 
        #     text="Threshold", 
        #     font=("Helvetica", 14, 'bold'), fg='#f00'
        # ).grid(column=0, row=1)

        # threshold_entry = tk.Entry(tk_wdw, readonlybackground="white")
        # threshold_entry.insert(0, peak_picking_threshold)
        # threshold_entry.grid(column=1, row=1)
        # refreshed_threshold = { "th" : None }

        # tk.Button(
        #     tk_wdw, 
        #     text="Refresh & Close", 
        #     fg = "orange", 
        #     font=("Helvetica", 20),        
        #     command=lambda: refresh_ui(refreshed_threshold, threshold_entry)
        # ).grid(column = 0, row = npeaks+3 if npeaks else 4)  
        
        # tk.Button(
        #     tk_wdw, 
        #     text="Save & Close", 
        #     fg = "blue", 
        #     font=("Helvetica", 20),        
        #     command=lambda: save_info_clustering(user_input, Res)
        # ).grid(column = 1, row = npeaks+3 if npeaks else 4) 

        # tk.Button(
        #     tk_wdw, 
        #     text="Exit", 
        #     fg = "black", 
        #     font=("Helvetica", 20),        
        #     command=lambda: Exit()
        # ).grid(column = 2, row = npeaks+3 if npeaks else 4) 

    tk_wdw.mainloop()
    # if refreshed_threshold["th"]:
    #     return float(refreshed_threshold["th"])
    # else:
    #     return None

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

    figure1 = plt.Figure(figsize=(6,5), dpi=100)
    ax1 = figure1.add_subplot(111)
    ax1.plot(x_spec, y_spec, '-',color='teal')
    for i in range(n_peak):
        ax1.plot(
            peak_picking_data.Peak_Position.iloc[i],
            peak_picking_data.Peak_Intensity.iloc[i],
            c=colors[i],
            ls='none',
            marker='o'
            )
    ax1.axhline(peak_picking_threshold,c='r')
    ax1.invert_xaxis()
    ax1.set_xlabel(r'$^1H$ $(ppm)$')
    return figure1, colors 

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

def progress_bar_exit(root):
    root.destroy()


