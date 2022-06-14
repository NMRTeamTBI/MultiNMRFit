from re import L
import tkinter
import tkinter.messagebox
import random

import os
import sys
import json
from pathlib import Path 
import tkinter as tk
from tkinter import simpledialog, ttk, messagebox
import PyPDF2
import logging
import webbrowser
import pandas as pd
# Import plot libraries
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkPDFViewer import tkPDFViewer as pdf

import multinmrfit
import multinmrfit.io as nio
import multinmrfit.run as nrun
import multinmrfit.utils_nmrdata as nfu
import multinmrfit.fitting as nff


class LoadingUI:
    def __init__(self, frame, user_input, *args, **kwargs):
        self.frame = frame

        # # ============ create subframes ============
        self.frame_inputs = tk.LabelFrame(frame,width=250,height=250,text="Inputs",foreground='blue')
        self.frame_analysis = tk.LabelFrame(frame,width=250,height=250,text="Analysis",foreground='blue')
        self.frame_output = tk.LabelFrame(frame,width=250,height=200,text="Outputs",foreground='blue')
        self.frame_options = tk.LabelFrame(frame,width=250,height=300,text="Options",foreground='blue')

        self.frame_inputs.grid(row=0,column=0, columnspan=2, padx=3, pady=3)
        self.frame_analysis.grid(row=0,column=2, columnspan=2, padx=3, pady=3)
        self.frame_output.grid(row=1,column=0, columnspan=2, padx=3, pady=3,sticky='N')
        self.frame_options.grid(row=1,column=2, columnspan=2, padx=3, pady=3)

        # # ============ create Buttons ============
        self.load_button = tk.Button(frame,text=" Load ",foreground='black',command=lambda:nio.load_config_file(frame,user_input))
        self.load_button.grid(row=2, column=0, padx=3, pady=5)

        self.save_button = tk.Button(frame,text=" Save ",foreground='black',command=lambda:self.save_config_file({k: v.get() for k, v in user_input.items()}))
        self.save_button.grid(row=2, column=1, padx=3, pady=5)

        # self.run_button = tk.Button(frame,text=" Run ",foreground='black',command=lambda:self.App_Run(user_input))
        # self.run_button.grid(row=2, column=2, padx=3, pady=5)

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


            # # ============ Options ============

            self.input_raws_label = tk.Label(self.frame_options,text='Data row no (* 2D only):',justify=tk.CENTER,foreground='black')
            self.input_raws_label.place(relx=0.05, rely=0.08, anchor="w")

            self.input_raws = tk.StringVar()
            self.input_raws_entry = tk.Entry(self.frame_options,textvariable=self.input_raws,bg='white',fg='black',borderwidth=0,state='disabled' if user_input['analysis_type'] == '1D_Series' else 'normal')
            self.input_raws_entry.place(relx=0.1, rely=0.16, width=200, anchor=tkinter.W)
            user_input['option_data_row_no'] = self.input_raws

            # Use previous fit results as starting parameters
            self.TimeSeries = tk.BooleanVar()
            self.check_box_opt2 = tk.Checkbutton(self.frame_options,text="Use previous fit",variable=self.TimeSeries,foreground='black')
            self.check_box_opt2.place(relx=0.05, rely=0.28, anchor=tkinter.W)
            user_input['option_previous_fit'] = self.TimeSeries
            
            # Use Offset in Fitting
            self.Offset = tk.BooleanVar()
            self.check_box_opt3 = tk.Checkbutton(self.frame_options,text="Offset",variable=self.Offset,foreground='black')
            self.check_box_opt3.place(relx=0.05, rely=0.40, anchor=tkinter.W)
            user_input['option_offset'] = self.Offset

            # # Verbose Log
            self.VerboseLog = tk.BooleanVar()
            self.check_box_opt4 = tk.Checkbutton(self.frame_options,text="Verbose log",variable=self.VerboseLog,foreground='black')
            self.check_box_opt4.place(relx=0.05, rely=0.52, anchor=tkinter.W)
            user_input['option_verbose_log'] = self.VerboseLog

            # # Verbose Log
            self.mergepdf = tk.BooleanVar()
            self.check_box_opt5 = tk.Checkbutton(self.frame_options,text="Merge pdf(s)",variable=self.mergepdf,foreground='black')
            self.check_box_opt5.place(relx=0.05, rely=0.64, anchor=tkinter.W)
            user_input['option_merge_pdf'] = self.mergepdf

            # optimization algorithm
            self.optimizer_label = tk.Label(self.frame_options,text='Optimization algorithm:',justify=tk.CENTER,foreground='black')
            self.optimizer_label.place(relx=0.05, rely=0.76, anchor="w")
            vals = ['L-BFGS-B', 'DE + L-BFGS-B']
            self.optimizer = tk.StringVar()
            self.optimizer.set(vals[0])
            self.optimizer_BFGS = tk.Radiobutton(self.frame_options, variable=self.optimizer, text=vals[0], value=vals[0],foreground='black')
            self.optimizer_BFGS.place(relx=0.05, rely=0.84, anchor=tkinter.W)
            self.optimizer_DE_BFGS = tk.Radiobutton(self.frame_options, variable=self.optimizer, text=vals[1], value=vals[1],foreground='black')
            self.optimizer_DE_BFGS.place(relx=0.5, rely=0.84, anchor=tkinter.W)
            user_input['option_optimizer'] = self.optimizer

    def update_analysis_type(self, event):
        if self.analysis_type_cb.get() == "Pseudo2D":
            self.check_box_opt2.select()
        else:
            self.check_box_opt2.deselect()

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

    def App_Run(self, user_input):
        user_input = nio.check_input_file({k: v.get() for k, v in user_input.items()},self.frame)
        nrun.run_analysis(user_input,self)
        self.on_closing()

class ProcessingUI:

    def __init__(self, master, user_input, frame, *args, **kwargs):

        self.frame = frame
        # # self.peak_picking_threshold = peak_picking_threshold
        # # self.df_var = tk.StringVar()


        # # # ============ create TkFrames ============
        self.frame_graph = tk.LabelFrame(frame,width=600,height=500,text="Reference spectrum",foreground='blue')
        self.frame_peak_Table = tk.LabelFrame(frame,width=600,height=570,text="Clustering information",foreground='blue')

        self.frame_graph.grid(row=0,column=0, sticky="nesw", padx=3, pady=5)
        self.frame_peak_Table.grid(row=1, column=0, sticky="nsew", padx=3, pady=5, columnspan=3)

                ######################################################
        ##################### Read and Load Data #############
        ######################################################
        self.intensities, x_ppm = nfu.retrieve_nmr_data(user_input) 
        print('Loading -- Complete')
        #-----------------------------------------------------#    

        ######################################################
        #Extract data within the region selected by the user##
        ######################################################
        print('Extraction of NMR Data')
        self.intensities, x_ppm = nfu.Extract_Data(
            data     = self.intensities,
            x_ppm    = x_ppm,
            x_lim    = [user_input['spectral_limits'][0],user_input['spectral_limits'][1]]
        )
        print('Extraction -- Complete')
        #-----------------------------------------------------#
        
        if user_input['analysis_type'] == 'Pseudo2D':
            self.idx_ref = int(user_input['reference_spectrum' ]) - 1  
        else:            
            self.idx_ref = user_input['data_exp_no'].index(int(user_input['reference_spectrum' ]))

        ######################################################
        ###########Extract the reference spectrum#############
        ######################################################
        if user_input['analysis_type'] == 'Pseudo2D':
            self.intensities_reference_spectrum = self.intensities[self.idx_ref,:]
            self.x_ppm_reference_spectrum = x_ppm
        elif user_input['analysis_type'] == '1D_Series':
            self.intensities_reference_spectrum = self.intensities[self.idx_ref,:]
            self.x_ppm_reference_spectrum = x_ppm[self.idx_ref,:]
        #-----------------------------------------------------#   

        ######################################################
        ##############Peak Picking/ Clustering################
        ######################################################
        threshold = user_input['threshold']

        clustering_results = pd.DataFrame(columns=['Peak_Position','Peak_Intensity','Selection','Cluster','Options'])

        #     # # ============ Figure ============
        peak_picking_data = self.peak_picking(self.x_ppm_reference_spectrum, self.intensities_reference_spectrum, threshold)
        colors = self.create_plot(self.x_ppm_reference_spectrum, self.intensities_reference_spectrum, threshold,peak_picking_data)
        # self.clustering_information = self.create_table(peak_picking_data,colors) 
        self.create_table(peak_picking_data,colors)
        # print(clustering_res)

        self.run = tk.Button(frame,text=" Run Fitting ",foreground='black',command=lambda:[self.save_info_clustering(clustering_results),self.prepare_data_to_fit(master, frame, self.clustering_table, user_input)])
        self.run.place(relx=0.1, rely=0.97,width=150, anchor=tkinter.W)

    def peak_picking(self, x_spec_ref, y_spec_ref, threshold):
        peak_picking = nfu.Peak_Picking_1D(x_data = x_spec_ref, y_data = y_spec_ref, threshold = threshold)
        peak_picking = nfu.sort_peak_picking_data(peak_picking, 15)        
        return peak_picking

    def create_table(self,peak_picking_data,colors):
        n_peak = len(peak_picking_data)
        self.clustering_information = {'Peak Position' : [], 'Peak Intensity' : [], 'Cluster ID' : [], 'Options' : []}

        options = ['Roof'] # options
    
        frame_canvas = tk.Frame(self.frame_peak_Table)
        frame_canvas.grid(row=2, column=0, pady=(5, 0), sticky='nw')
        frame_canvas.grid_rowconfigure(0, weight=1)
        frame_canvas.grid_columnconfigure(0, weight=1)
        # Set grid_propagate to False to allow 5-by-5 buttons resizing later
        frame_canvas.grid_propagate(False)

        canvas = tk.Canvas(frame_canvas)
        canvas.grid(row=0, column=0, sticky="news")

        # Linxk a scrollbar to the canvas
        vsb = tk.Scrollbar(frame_canvas, orient="vertical", command=canvas.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        canvas.configure(yscrollcommand=vsb.set)

        # Create a frame to contain the buttons
        frame_buttons = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame_buttons, anchor='nw')

        if n_peak == 0:
            self.th_label = tk.Label(
                frame_buttons, 
                text='No peak found, please lower the threshold',
                foreground='red'
            )
            self.th_label.place(relx=0.25, rely=0.7, anchor=tkinter.W)  

        else:
            n_rows = n_peak
            n_columns = 5

            c = 0 
            for label in self.clustering_information.keys():
                tk.Label(frame_buttons, text=label,foreground='black').grid(column=c+1, row=0,padx=2)
                c +=1

            # buttons = [[tk.Button() for j in range(columns)] for i in range(rows)]
            for i in range(0, n_rows):
                for j in range(0, n_columns):
                    if j == 0:
                        self.element = tk.Label(frame_buttons, text="Peak "+str(i+1),fg=colors[i])

                    elif j ==1:
                        self.element = tk.Entry(frame_buttons,justify = "center",background='white',foreground='black',width=10)
                        self.clustering_information['Peak Position'].append(self.element)
                        data = peak_picking_data.iloc[i].loc['Peak_Position']
                        self.element.insert(0, round(data,3))

                    elif j ==2:
                        self.element = tk.Entry(frame_buttons,justify = "center",background='white',foreground='black',width=10)
                        self.clustering_information['Peak Intensity'].append(self.element)
                        data = peak_picking_data.iloc[i].loc['Peak_Intensity']
                        self.element.insert(0, round(data,3))

                    elif j ==3:
                        self.element = tk.Entry(frame_buttons,justify = "center",background='white',foreground='black',width=10)
                        self.clustering_information['Cluster ID'].append(self.element)

                    elif j == 4:
                        self.element = ttk.Combobox(frame_buttons, values=options,width=10)
                        self.clustering_information['Options'].append(self.element)


                    else:
                        self.element = tk.Entry(frame_buttons,justify = "center", background='white',foreground='black',width=10)
                    self.element.grid(row=i+1, column=j, sticky='news')

            # Update buttons frames idle tasks to let tkinter calculate buttons sizes
            frame_buttons.update_idletasks()

            # Resize the canvas frame to show exactly 5-by-5 buttons and the scrollbar
            # first5columns_width = sum([buttons[0][j].winfo_width() for j in range(0, 5)])
            # first5rows_height = sum([buttons[i][0].winfo_height() for i in range(0, 5)])
            frame_canvas.config(width=500,
                                height=120)

            # Set the canvas scrolling region
            canvas.config(scrollregion=canvas.bbox("all"))

    def save_info_clustering(self, clustering_table):

        clustering_table.Peak_Intensity = [i.get() for i in self.clustering_information["Peak Intensity"]]
        clustering_table.Peak_Position =  [i.get() for i in self.clustering_information["Peak Position"]]
        clustering_table.Options = [i.get() for i in self.clustering_information["Options"]]
        clustering_table.Cluster = [i.get() for i in self.clustering_information["Cluster ID"]]
        clustering_table.Selection = [True if i.get() != '' else False for i in self.clustering_information["Cluster ID"]]

        if not True in clustering_table.Selection.tolist():
            messagebox.showerror("Error", 'No peak selected. Select at least one signal.')
        self.clustering_table = clustering_table

    def create_plot(self, x_spec, y_spec, threshold,peak_picking_data):
        
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

    def prepare_data_to_fit(self, master, frame, clustering_table, user_input):
        self.user_picked_data = clustering_table[clustering_table["Selection"].values]
        self.user_picked_data = nfu.filter_multiple_clusters(self.user_picked_data)
        self.user_picked_data.Peak_Intensity = self.user_picked_data.Peak_Intensity.apply(pd.to_numeric)
        # self.user_picked_data = self.user_picked_data.apply(pd.to_numeric)
        self.scaling_factor = self.user_picked_data.Peak_Intensity.mean()

        ######################################################
        #Prepare spectral list with all required indices##
        ######################################################
        # (id, expno, procno, rowno, output_name)
        if user_input['analysis_type'] == "Pseudo2D" : 
            if not len(user_input.get('option_data_row_no',[])):
                user_input['option_data_row_no'] = np.arange(1,len(self.intensities)+1,1)
            self.spectra_to_fit = [(j-1, i, user_input['data_exp_no'][0], user_input['data_proc_no'], j, j) for i,j in enumerate(user_input['option_data_row_no'])]
        elif user_input['analysis_type'] == '1D_Series':
                self.spectra_to_fit = [(i, i, j, user_input['data_proc_no'], 1, j) for i, j in enumerate(user_input['data_exp_no'])]

        ######################################################
        #Check to use the previpous fit as initial values for fitting##
        ######################################################
        self.use_previous_fit = user_input['option_previous_fit']

        self.offset = user_input['option_offset']
        self.merged_pdf = user_input['option_merge_pdf']
 
        fit_results_table, stat_results_table = nff.full_fitting_procedure(
            intensities         =   self.intensities,
            x_spec              =   self.x_ppm_reference_spectrum,
            ref_spec            =   self.idx_ref,
            peak_picking_data   =   self.user_picked_data,
            scaling_factor      =   self.scaling_factor,
            spectra_to_fit      =   self.spectra_to_fit,
            use_previous_fit    =   self.use_previous_fit,
            offset              =   self.offset
        )
        nio.save_output_data(
            user_input          ,
            fit_results_table   ,
            stat_results_table   ,
            self.intensities         ,
            self.x_ppm_reference_spectrum,
            self.spectra_to_fit,
            self.user_picked_data,
            self.scaling_factor,
            offset=self.offset,
            merged_pdf = self.merged_pdf)

        self.plot_button = tk.Button(frame,text=" Visualization ",foreground='black',command=lambda:self.create_plot_frame(master, user_input))
        self.plot_button.place(relx=0.6, rely=0.97,width=150, anchor=tkinter.W)

    def create_plot_frame(self, master, user_input):
        frame = tk.LabelFrame(master,width=400,height=600,text=f"Visualisation",foreground='red')
        frame.grid(row=0,column=2, sticky="nsew")

        frame_spectra = tk.LabelFrame(frame,width=400,height=300,text=f"Spectra",foreground='red')
        frame_spectra.grid(row=0,column=2, sticky="nsew")

        frame_params = tk.LabelFrame(frame,width=400,height=300,text=f"Paremters",foreground='red')
        frame_params.grid(row=1,column=2, sticky="nsew")

        PlottingUI(
            frame_spectra,
            frame_params,
            user_input, 
            self.x_ppm_reference_spectrum, 
            self.user_picked_data, 
            self.scaling_factor

            )

class PlottingUI:
    def __init__(self, frame_spectra, frame_params, user_input, x_scale, peak_picking_data, scaling_factor, *args, **kwargs):
        
        self.frame_params = frame_params
        self.frame_spectra = frame_spectra

        d_id = nff.get_fitting_parameters(peak_picking_data, x_scale, scaling_factor)[0]
        cluster_list = nio.getList(d_id)

        # self.cluster_id_List = cluster_list

        output_path         =   user_input['output_path']
        output_folder       =   user_input['output_folder']
        output_name         =   user_input['output_name']

        file_list = []
        self.fname = Path(output_path,output_folder)#+'_'+str(_multiplet_type_)+'_'+str(self.cluster_id_variable.get())+'_fit.txt')
        for file in os.listdir(self.fname):
            if file.startswith(output_name) and file.endswith("fit.txt"):
                for cluster in cluster_list:
                    if cluster in file:
                        file_list.append(file)


        self.cluster_id_variable = tk.StringVar(frame_params)
        # self.cluster_id_variable.set('')
        self.cluster_id_opt = tk.OptionMenu(frame_params, self.cluster_id_variable, *file_list, command= self.OptionMenu_SelectionEvent)
        self.cluster_id_opt.place(relx=0.05, rely=0.05,width=300, anchor=tkinter.W)
        self.cluster_id_opt.config(fg="BLACK", activebackground="BLACK", activeforeground="BLACK")

    def OptionMenu_SelectionEvent(self, event):
        full_fname = Path(self.fname,str(self.cluster_id_variable.get()))
        self.data = pd.read_csv(full_fname,sep='\t')
        params = list(self.data.columns[3:])

        self.parameters_List = params
        self.parameters_variable = tk.StringVar(self.frame_params)
        # self.parameters_variable.set(self.parameters_List[0])
        self.parameters_opt = tk.OptionMenu(self.frame_params, self.parameters_variable, *self.parameters_List, command= self.OptionMenu_PlotEvent)
        self.parameters_opt.config(fg="BLACK", activebackground="BLACK", activeforeground="BLACK")
        self.parameters_opt.place(relx=0.05, rely=0.14,width=300, anchor=tkinter.W)

    def OptionMenu_PlotEvent(self, event):
        
        fig = plt.Figure()
        ax = fig.subplots(1,1)
        ax.plot(
            self.data.loc[:,'exp_no'].tolist(),
            self.data.loc[:,self.parameters_variable.get()].tolist(),
            marker='o',
            color='blue'
            )

        canvas = FigureCanvasTkAgg(fig, self.frame_params)
        canvas.draw()
        canvas.get_tk_widget().place(relx=0.05, rely=0.6,width=380, height=200, anchor=tkinter.W)

        v1 = pdf.ShowPdf()
        
        # Adding pdf location and width and height.
        v2 = v1.pdf_view(self.frame_spectra,
                        pdf_location = '~/Documents/Research/Data_Analysis/TEST_Multinmrfit/Guy/myself/plot_ind/MHET_4_1.pdf' , 
                        width = 50, height = 100)

        v2.pack()
  

        # nio.plot_gui(user_input, x_scale, peak_picking_data, scaling_factor,fit_results, stat_results, spectra_to_fit, offset=False)
        # self.stat_results_table   ,

class App:

    def __init__(self, user_input, *args, **kwargs):
        APP_NAME = f"Multinmrfit Interface (v{multinmrfit.__version__})"

        super().__init__(*args, **kwargs)
        self.master = tk.Tk()
        self.master.title(APP_NAME)
        self.master.resizable(False, False)
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

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

        # Definitions of the general frames
        self.loading_frame = tk.LabelFrame(self.master,width=500,height=600,text="Reference spectrum",foreground='red')
        self.loading_frame.grid(row=0,column=0, sticky="nsew")


        self.loading = LoadingUI(self.loading_frame, user_input)


        var = tk.IntVar()
        self.run_button = tk.Button(self.loading_frame,text=" Clustering ",foreground='black',command=lambda:[var.set(1),self.create_visu_frame(user_input)])
        self.run_button.grid(row=2, column=2, padx=3, pady=5)
        self.run_button.wait_variable(var)

    def on_closing(self, event=0):
        self.master.destroy()
        exit()

    def create_visu_frame(self,user_input):

        user_input = nio.check_input_file({k: v.get() for k, v in user_input.items()},self.master)
        if isinstance(user_input,dict):
            if user_input.get('valid',False):   
                frame = tk.LabelFrame(self.master,width=800,height=600,text=f"Peak Picking Visualisation and Clustering",foreground='red')
                frame.grid(row=0,column=1, sticky="nsew")
                ProcessingUI(self.master, user_input, frame)

    def start(self):
        self.master.mainloop()


# app = App(user_input=nio.create_user_input())
# app.start()

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
