# Import system libraries
from pathlib import Path 
import logging
from tkinter import simpledialog, ttk, filedialog
# Import math libraries
import pandas as pd
import numpy as np
import json
import os
# Import plot libraries
import matplotlib.pyplot as plt

# Import our own libraries
import multinmrfit.fitting as nff
import multinmrfit.multiplets as nfm
import multinmrfit.ui as nui

import natsort 
from PyPDF2 import PdfFileMerger
import string

logger = logging.getLogger()

#############Input
def create_user_input():
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
    return user_input  

def load_config_file(self=None, user_input=None, config_file_path=None):
        if self and self.winfo_exists():
            config_file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.json")])
            if not config_file_path:
                return None
        try:
            f = open(str(Path(config_file_path)),"r")    
        except FileNotFoundError:
            error_handling(self,'Config file not found')
            return None

        try:
            config = json.loads(f.read())
        except json.decoder.JSONDecodeError as e:
            error_handling(self,'Json config file must be reformated')
            return None
        except UnicodeDecodeError as e:
            error_handling('Wrong config file type (not a json file, see example)')
            return None

        if self and self.winfo_exists():
            options_list = ['option_data_row_no','option_previous_fit','option_offset','option_verbose_log']
            for label in user_input.keys():                
                if label in options_list:
                    if label not in config.keys():
                        pass
                    else:
                        user_input[label].set(config.get(label, ''))
                else:
                    user_input[label].set(config.get(label, ''))
            return user_input
        else:
            return config

def create_spectra_list(user_input):
    # check for allowed characters
    allowed = set(string.digits + ',' + '-')
    if not set(user_input) <= allowed:
        # TO BE UPDATED: DISPLAY ERROR MESSAGE & STOPS
        logging.error("Wrong format for experiments list.")
    # create list
    experiment_list = []
    for i in user_input.split(','):
        if "-" in i:
            spectra = i.split('-')
            try:
                if int(spectra[0]) <= int(spectra[1]):
                    experiment_list += range(int(spectra[0]), int(spectra[1])+1)
                else:
                    experiment_list += range(int(spectra[1]), int(spectra[0])+1)
            except:
                # TO BE UPDATED: DISPLAY ERROR MESSAGE & STOPS
                logging.error("Experiments/rows to process should be positive integers.")
        else:
            experiment_list.append(int(i))
    return experiment_list

def error_handling(self,message, critical_error=False):
    if self and self.winfo_exists():
        app_err = nui.App_Error(message)
        app_err.start()
    elif logger:
        logger.error(message)    
    if critical_error is True:
        exit()
  
def check_input_file(user_input,self=None):

    if self and self.winfo_exists():
        is_gui = True
        is_not_gui = False
    else:
        is_gui = False
        is_not_gui = True

    try:
        output_dir = Path(user_input.get('output_path'),user_input.get('output_folder'))
        if not output_dir:
            return error_handling("Argument : 'output_folder' is missing", critical_error=is_not_gui)
        output_dir.mkdir(parents=True,exist_ok=True)

        # create logger (should be root to catch builder and simulator loggers)
        logger = logging.getLogger()
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
        # set log level
        log_level = logging.DEBUG if user_input.get('verbose_log') else logging.INFO
        logger.setLevel(log_level)

        if not Path(user_input.get('data_path')).exists():
            return error_handling(self,"Argument : 'data_path' does not exist", critical_error=is_not_gui)

        # if not Path(user_input.get('data_path'),user_input.get('data_folder')).exists():
        #     print('hello')
        #     return error_handling(self,"Argument : 'data_folder' does not exist", critical_error=is_not_gui)

        if float(user_input.get('threshold', 1)) <= float(0):
            return error_handling(self,"Argument : 'threshold' is too low (should be > 0)", critical_error=is_not_gui)

        if user_input.get('analysis_type') not in ['Pseudo2D', '1D', '1D_Series']:
            return error_handling(self,"Argument : 'analysis_type' expected as 'Pseudo2D','1D' or '1D_Series", critical_error=is_not_gui)

        if not user_input.get('spectral_limits'):
            return error_handling(self,"Argument : 'spectral_limits' is missing" , critical_error=is_not_gui)

        spec_lim = [float(i) for i in user_input.get('spectral_limits').split(',')]

        if len(spec_lim)%2 != 0 and len(spec_lim) != 0:
            return error_handling(self,"Argument : 'spectral_limits' is incomplete", critical_error=is_not_gui)

        exp_list = create_spectra_list(user_input.get('data_exp_no'))
        for exp in exp_list:
            if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp)).exists():
                return error_handling(self,f"Argument : experiment <{exp}> does not exist", critical_error=is_not_gui)
            else:
                if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp),'pdata',user_input.get('data_proc_no')).exists():
                    return error_handling(self,f"Argument : experiment/procno <{exp}/{user_input.get('data_proc_no')}> does not exist", critical_error=is_not_gui)

        if user_input.get('analysis_type') != 'Pseudo2D' and int(user_input.get('reference_spectrum')) not in exp_list:
            return error_handling(self,f"Argument : reference_spectrum <{user_input.get('reference_spectrum')}> not found in experiment list", critical_error=is_not_gui)

        row_list = []
        if user_input.get('option_data_row_no'):
            row_list = create_spectra_list(user_input.get('option_data_row_no'))
            if int(user_input.get('reference_spectrum')) not in row_list :
                return error_handling(self,f"Argument : reference_spectrum <{user_input.get('reference_spectrum')}> not found in row list", critical_error=is_not_gui)

        config = {
            'data_path'             :   user_input.get('data_path'),
            'data_folder'           :   user_input.get('data_folder'),
            'data_exp_no'           :   exp_list,
            'data_proc_no'          :   user_input.get('data_proc_no'),
            'reference_spectrum'    :   user_input.get('reference_spectrum'),
            'analysis_type'         :   user_input.get('analysis_type'),
            'spectral_limits'       :   spec_lim,
            'threshold'             :   float(user_input.get('threshold', 0)),
            'output_path'           :   user_input.get('output_path'),
            'output_folder'         :   user_input.get('output_folder'),
            'output_name'           :   user_input.get('output_name'),
            'data_row_no'           :   row_list,
            'previous_fit'          :   user_input.get('option_previous_fit', False),
            'offset'                :   user_input.get('option_offset', False),
            'verbose_log'           :   user_input.get('option_verbose_log', False)

        }

    except Exception as e:
        return error_handling(self,e, critical_error=is_not_gui)

    # Options
    options_list = ['data_row_no','previous_fit','offset','verbose_log']

    if config['analysis_type'] != 'Pseudo2D': 
        config.pop("data_row_no")
    if config['analysis_type'] == 'Pseudo2D': 
        config.pop("previous_fit")
        if config['data_row_no'] == []:
           config.pop("data_row_no") 
    
    for key, conf in config.items():        
        if key not in options_list and conf is None:
            return error_handling(self,f"Argument : '{key}' is missing", critical_error=is_not_gui)
    if is_gui:
        self.destroy()
    logger.info(json.dumps(config,indent=4))

    return config

#############Output
def getList(dict):
    return [k for k in dict.keys()]

def getIntegral(x_fit, _multiplet_type_, fit_par):
    d_mapping = nfm.mapping_multiplets()[0]
    _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
    y = _multiplet_type_function(x_fit, *fit_par)
    integral = np.sum(y)*(x_fit[1]-x_fit[0])
    return integral
    
def single_plot_function(r, x_scale, intensities, fit_results, x_fit, d_id, scaling_factor, output_path, output_folder, output_name, offset=False):    
    fig, ax = plt.subplots(1, 1)
    fig.set_size_inches([11.7,8.3])

    ax.plot(
        x_scale,
        intensities[r[0],:],
        color='b',
        ls='None',
        marker='o',
        markersize=7
        )    
    ax.invert_xaxis()
    res = fit_results.iloc[r[1],:].values.tolist()

    sim = nff.simulate_data(
        x_fit,
        res,
        d_id,
        scaling_factor,
        offset=offset
        )

    ax.plot(
        x_fit, 
        sim, 
        'r-', 
        lw=1,
        label='fit')

    res_num = r[5]
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

def build_output(d_id_i, x_fit, fit_results, scaling_factor,spectra_to_fit):
    
    # get multiplicity, names & values of parameters to initialize the dataframe
    _multiplet_type_ = d_id_i[2]
    col = range(d_id_i[1][0],d_id_i[1][1])
    mutliplet_results = fit_results[fit_results.columns.intersection(col)]
    d_mapping, _ = nfm.mapping_multiplets()
    mutliplet_results.columns = d_mapping[_multiplet_type_]['params']

    # calculate integral & intensity
    mutliplet_results["integral"] = [scaling_factor*getIntegral(x_fit, _multiplet_type_, row.tolist()) for _, row in mutliplet_results.iterrows()]
    mutliplet_results["Amp"] *= scaling_factor

    # append IDs
    mutliplet_results.insert(loc = 0, column = 'exp_no' , value = [i[2] for i in spectra_to_fit])
    mutliplet_results.insert(loc = 1, column = 'proc_no' , value = [int(i[3]) for i in spectra_to_fit])
    mutliplet_results.insert(loc = 2, column = 'row_id' , value = [i[4] for i in spectra_to_fit])

    return _multiplet_type_, mutliplet_results

def update_results(mutliplet_results, fname):
    try:
        original_data = pd.read_csv(str(fname), sep="\t")
    except:
        logger.error("Error when opening existing results file.")
    condition = ((original_data['exp_no'].isin(mutliplet_results['exp_no'])) & (original_data['proc_no'].isin(mutliplet_results['proc_no'])) & (original_data['row_id'].isin(mutliplet_results['row_id'])))
    tmp = original_data.loc[[not x for x in condition],:]

    return pd.concat([tmp, mutliplet_results])

def output_txt_file(x_fit,fit_results, d_id, scaling_factor,spectra_to_fit,output_path, output_folder,output_name):
    
    cluster_list = getList(d_id)
    for i in cluster_list:
        # create output dataframe
        _multiplet_type_, mutliplet_results = build_output(d_id[i], x_fit, fit_results, scaling_factor,spectra_to_fit)
        # update results file if already exists
        fname = Path(output_path,output_folder,output_name+'_'+str(_multiplet_type_)+'_'+str(i)+'.txt')
        if fname.is_file():
            mutliplet_results = update_results(mutliplet_results, fname)
        # sort results by exp_no, proc_no & row_id
        mutliplet_results = mutliplet_results.sort_values(['exp_no', 'proc_no', 'row_id'], ascending=(True, True, True))
        # save to tsv
        mutliplet_results.to_csv(
            str(fname), 
            index=False, 
            sep = '\t'
            )
    logger.info('Save data to text file -- Complete')

def merge_pdf(output_path,output_folder,output_name):
    path_individual_plots = Path(output_path,output_folder,'plot_ind')
    path_final_plot = Path(output_path,output_folder)

    # read all pdf in directory and sort them
    pdfs = os.listdir(path_individual_plots)
    pdfs_clear = []
    for pdf in pdfs:
        if pdf.startswith(output_name):
            pdfs_clear.append(pdf)
    pdfs_clear = natsort.natsorted(pdfs_clear,reverse=False)

    # merge all pdfs and create a single one 
    merger = PdfFileMerger()
    for pdf in pdfs_clear:
        if pdf.startswith(output_name):
            merger.append(str(Path(path_individual_plots,pdf)))
    
    output_pdf = str(Path(path_final_plot,output_name+'_'+'Spectra_Full.pdf'))
    merger.write(output_pdf)
    merger.close()

def save_output_data(user_input, fit_results, intensities, x_scale, spectra_to_fit, peak_picking_data, scaling_factor, offset=False):

    output_path         =   user_input['output_path']
    output_folder       =   user_input['output_folder']
    output_name         =   user_input['output_name']

    x_fit = np.linspace(np.min(x_scale),np.max(x_scale),2048)
    d_id = nff.get_fitting_parameters(peak_picking_data, x_fit, scaling_factor)[0]

    fit_results = fit_results.apply(pd.to_numeric)
    Path(output_path,output_folder).mkdir(parents=True,exist_ok=True)

    logger.info('Save data to text file ') 
    output_txt_file(x_fit,fit_results, d_id, scaling_factor,spectra_to_fit,output_path, output_folder,output_name)
    logger.info('Save data to text file -- Complete')

    logger.info('Save plot to pdf')
    for r in spectra_to_fit:
        single_plot_function(
                r, 
                x_scale, 
                intensities,        
                fit_results, 
                x_fit, 
                d_id, 
                scaling_factor, 
                output_path,   
                output_folder,
                output_name,
                offset=offset
            )
    merge_pdf(output_path,output_folder,output_name)
    logger.info('Save plot to pdf -- Complete')