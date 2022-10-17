# Import system libraries
from pathlib import Path 
import logging
from tkinter import filedialog, messagebox
import ast
# Import math libraries
import pandas as pd
import numpy as np
import json
import os
# Import plot libraries
import matplotlib.pyplot as plt

import natsort 
from PyPDF2 import PdfFileMerger
import string

# Import our own libraries
import multinmrfit.fitting as nff
import multinmrfit.multiplets as nfm

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
    'option_constraints_window':   None
    }
    return user_input  

def load_config_file(gui=None, user_input=None, config_file_path=None):
        if gui and gui.winfo_exists():
            config_file_path = filedialog.askopenfilename(filetypes=[("All Files", "*.json")])
            if not config_file_path:
                return None
        try:
            f = open(str(Path(config_file_path)),"r")    
        except FileNotFoundError:
            error_handling(gui,'Config file not found')
            return None

        try:
            print(f)
            config = json.loads(f.read())
        except json.decoder.JSONDecodeError as e:
            error_handling(gui,'Wrong config file format, please check and correct the file (see example)')
            return None
        except UnicodeDecodeError as e:
            error_handling('Wrong config file type (not a json file, see example)')
            return None

        if gui and gui.winfo_exists():
            options_list = ['option_data_row_no','option_previous_fit','option_offset','option_verbose_log','option_merge_pdf', 'option_constraints_window']
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

def create_spectra_list(user_input, gui=None):
    # check for allowed characters
    allowed = set(string.digits + ',' + '-')
    if not set(user_input) <= allowed:
        # TO BE UPDATED: DISPLAY ERROR MESSAGE & STOPS
        error_handling(gui,"Argument : 'data_exp_no' has a wrong format")
        # logging.error("Wrong format for experiments list.")
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
                error_handling(gui,"Experiments/rows to process should be positive integers. \n Argument : 'data_exp_no' needs to be checked")
                # logging.error("Experiments/rows to process should be positive integers.")
        else:
            experiment_list.append(int(i))
    return experiment_list

def error_handling(gui,message):
    if gui and gui.winfo_exists(): 
        critical_error=False
        messagebox.showerror("Error", message)
    elif logger:
        critical_error=True
        logger.error(message)    
    if critical_error:
        exit()

def check_float(potential_float):
    try:
        float(potential_float)
        return True
    except ValueError:
        return False

def check_input_file(user_input,gui=None):

    try:
        ######### Check Output Path #########
        if not user_input.get('output_path'):
            return error_handling(gui,"Argument : 'output_path' is missing")
        ########################################################################

        ######### Check Output Folder #########
        if not user_input.get('output_folder'):
            return error_handling(gui,"Argument : 'output_folder' is missing")
        ########################################################################

        ######### Create output if needed #########
        try:
            output_dir = Path(user_input.get('output_path'),user_input.get('output_folder'))
        except:
            return error_handling(gui,"Check arguments 'output_path' and 'output_folder'.")

        try:
            output_dir.mkdir(parents=True,exist_ok=True)
        except:
            return error_handling(gui,"Cannot create output folder.")

        ########################################################################

        ######### Logger #########
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
        log_level = logging.DEBUG if user_input.get('option_verbose_log') else logging.INFO
        logger.setLevel(log_level)
        ########################################################################

        ######### Check Data Path #########

        if not user_input.get('data_path'):
            return error_handling(gui,"Argument : 'data_path' is missing")
        else:
            if user_input['data_path'].endswith('.csv'):
                pass
            elif not Path(user_input.get('data_path')).exists():
                return error_handling(gui,"Argument : 'data_path' does not exist")
        ########################################################################

        ######### Check Data Folder #########
        if user_input['data_path'].endswith('.csv'):
            pass
        else:
            if not user_input.get('data_folder'):
                return error_handling(gui,"Argument : 'data_folder' is missing")
            else:
                if not Path(user_input.get('data_path'),user_input.get('data_folder')).exists():
                    return error_handling(gui,"The path to the data is incorrect please check \n Argument : 'data_folder' or 'data_path' ")
        ########################################################################

        ######### Check ProcNo #########
        if user_input['data_path'].endswith('.csv'):
            pass
        else:
            if not user_input.get('data_proc_no'):
                return error_handling(gui,"Argument : 'data_proc_no' is missing")                      
            else:
                data_proc_no_check = check_float(user_input.get('data_proc_no'))
                if not data_proc_no_check:
                    return error_handling(gui,"Argument : 'data_proc_no' has a wrong type")
        ########################################################################

        ######### Check Exp List #########
        if user_input['data_path'].endswith('.csv'):
            exp_list = create_spectra_list(user_input.get('data_exp_no'),gui)
        else:
            if not user_input.get('data_exp_no'):
                return error_handling(gui,"Argument : 'data_exp_no' is missing")
            else:
                # The function create_spectra_list needs to be updated for error handling
                exp_list = create_spectra_list(user_input.get('data_exp_no'),gui)
            for exp in exp_list:
                if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp)).exists():
                    return error_handling(gui,f"Argument : experiment <{exp}> does not exist")
                else:
                    if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp),'pdata',user_input.get('data_proc_no')).exists():
                        return error_handling(gui,f"Argument : experiment/procno <{exp}/{user_input.get('data_proc_no')}> does not exist")

        ########################################################################

        ######### Check Threshold #########
        if not user_input.get('threshold'):
            return error_handling(gui,"Argument : 'threshold' is missing")          
        else:
            threshold_check = check_float(user_input.get('threshold'))
            if not threshold_check:
                return error_handling(gui,"Argument : 'threshold' has a wrong type")
            if threshold_check:
                if float(user_input.get('threshold',1)) <= float(0):
                    return error_handling(gui,"Argument : 'threshold' is too low (should be > 0)")
        ########################################################################

        ######### Check Limits #########
        if not user_input.get('spectral_limits'):
            return error_handling(gui,"Argument : 'spectral_limits' is missing")          
        else:
            spec_lim = [i for i in user_input.get('spectral_limits').split(',')]
            if len(spec_lim) > 2:
                return error_handling(gui,"Argument : 'spectral_limits' has more than tow entries")
            if len(spec_lim)%2 != 0 and len(spec_lim) != 0:
                return error_handling(gui,"Argument : 'spectral_limits' is incomplete")
            for limits in spec_lim:
                limit_check = check_float(limits)
                if not limit_check:
                    return error_handling(gui,"At lest one of the 'spectral_limits' has a wrong type")
            spec_lim = [float(i) for i in spec_lim]
            if not user_input['data_path'].endswith('.csv'):
                spec_lim.sort(reverse=True)
        ########################################################################

        ######### Check analysis type ######### 
        if not user_input.get('analysis_type'):
            return error_handling(gui,"Argument : 'analysis_type' is missing")          
        else:
            if user_input.get('analysis_type') not in ['Pseudo2D', '1D_Series']:
                return error_handling(gui,"Argument : 'analysis_type' expected as 'Pseudo2D'or '1D_Series \n (if you process a single 1D spectrum please use 1D_Series")
        ########################################################################

        # exp_list = create_spectra_list(user_input.get('data_exp_no'))
        # for exp in exp_list:
        #     if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp)).exists():
        #         return error_handling(gui,f"Argument : experiment <{exp}> does not exist")
        #     else:
        #         if not Path(user_input.get('data_path'),user_input.get('data_folder'),str(exp),'pdata',user_input.get('data_proc_no')).exists():
        #             return error_handling(gui,f"Argument : experiment/procno <{exp}/{user_input.get('data_proc_no')}> does not exist")

        ######### Check that reference exp belongs to the exp list ######### 
        if not user_input.get('reference_spectrum'):
            return error_handling(gui,"Argument : 'reference_spectrum' is missing")          
        else:
            if user_input.get('analysis_type') != 'Pseudo2D' and int(user_input.get('reference_spectrum')) not in exp_list:
                return error_handling(gui,f"Argument : reference_spectrum <{user_input.get('reference_spectrum')}> not found in experiment list")
        ########################################################################

        ######### Check that reference exp belongs to optionnal row list ######### 
        row_list = []
        if user_input.get('option_data_row_no'):
            row_list = create_spectra_list(user_input.get('option_data_row_no'))
            if int(user_input.get('reference_spectrum')) not in row_list :
                return error_handling(gui,f"Argument : reference_spectrum <{user_input.get('reference_spectrum')}> not found in row list")
        ########################################################################

        if user_input.get('option_constraints_window'):
            user_input['option_constraints_window'] = ast.literal_eval(user_input.get('option_constraints_window'))
        else:
            user_input['option_constraints_window'] = {"x0":0.001, "J":0.05, "lw":0.3}

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
            'option_data_row_no'    :   row_list,
            'option_previous_fit'   :   user_input.get('option_previous_fit', False),
            'option_offset'         :   user_input.get('option_offset', False),
            'option_verbose_log'    :   user_input.get('option_verbose_log', False),
            'option_merge_pdf'      :   user_input.get('option_merge_pdf', False),
            'option_constraints_window'    :   user_input['option_constraints_window'],
            'valid'                 :   True

        }
    
    except Exception as e:
        return error_handling(gui,e)

    # Options
    options_list = ['option_data_row_no','option_previous_fit','option_offset','option_verbose_log','option_merge_pdf', 'option_constraints_window']

    if config['analysis_type'] != 'Pseudo2D': 
        config.pop("option_data_row_no")
    else: 
        config["option_previous_fit"] = True
        if config['option_data_row_no'] == []:
           config.pop("option_data_row_no") 
    
    for key, conf in config.items():        
        if key not in options_list and conf is None:
            return error_handling(gui,f"Argument : '{key}' is missing")
    # if gui:
    #     gui.destroy()
        
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
    fig, [ax_rmsd,ax] = plt.subplots(2, 1, gridspec_kw={'height_ratios': [1, 4]})
    fig.set_size_inches([11.7,8.3])

    ax.plot(
        x_scale,
        intensities[r[0],:],
        color='r',
        ls='None',
        marker='o',
        markersize=2
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
    sim_rmsd = nff.simulate_data(
        x_scale,
        res,
        d_id,
        scaling_factor,
        offset=offset
    )

    rmsd = sim_rmsd-intensities[r[0],:]
    ax.plot(
        x_fit, 
        sim, 
        'r-', 
        lw=1,
        label='fit')
    ax.grid(axis='y')

    ax_rmsd.axhline(y=0,color='black',lw=1)
    ax_rmsd.grid(axis='y')
    ax_rmsd.plot(
        x_scale, 
        rmsd, 
        'r-', 
        ls='none',
        marker='o'
        )
    ax_rmsd.invert_xaxis()
    rmsd_max = max (max(rmsd), abs(min(rmsd)))

    ax_rmsd.set_ylim(-rmsd_max*1.3,rmsd_max*1.3)
    ax_rmsd.set_ylabel('Residuals')

    res_num = r[5]
    ax_rmsd.set_title("Spectra : " +str(res_num),fontsize=20)  
    ax.set_ylabel('Intensity')
    ax.set_xlabel('chemical shift (ppm)')

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
    #fig.set_size_inches([3,2])
    #plt.savefig(str(Path(path_2_save,output_name+'_'+str(res_num)+'.png')), format="png")
    plt.close(fig)

def build_output(d_id_i, x_fit, fit_results, stat_results, scaling_factor, spectra_to_fit, offset):
    
    # get multiplicity, names & values of parameters to initialize the dataframe
    _multiplet_type_ = d_id_i[2]

    col = range(d_id_i[1][0],d_id_i[1][1])
    mutliplet_results = fit_results[fit_results.columns.intersection(col)]
    mutliplet_stats = stat_results[stat_results.columns.intersection(col)]
    d_mapping, _ = nfm.mapping_multiplets()
    mutliplet_results.columns = d_mapping[_multiplet_type_]['params']
    mutliplet_stats.columns = d_mapping[_multiplet_type_]['params']

    # calculate integral & intensity
    cs_min = np.min([-2, np.min(x_fit)])
    cs_max = np.max([10, np.max(x_fit)])
    cs_step = (cs_max - cs_min) / 10000.
    cs = np.arange(cs_min, cs_max, cs_step)
    mutliplet_results["integral"] = [scaling_factor*getIntegral(cs, _multiplet_type_, row.tolist()) for _, row in mutliplet_results.iterrows()]
    mutliplet_results["Amp"] *= scaling_factor

    mutliplet_stats["Amp"] *= scaling_factor
    mutliplet_stats["integral"] = mutliplet_stats["Amp"] / mutliplet_results["Amp"] * mutliplet_results["integral"]
    
    if offset:
        mutliplet_results["offset"] = scaling_factor*fit_results.iloc[: , -1]
        mutliplet_stats["offset"] = scaling_factor*stat_results.iloc[: , -1]
    
    # append IDs
    mutliplet_results.insert(loc = 0, column = 'exp_no' , value = [i[2] for i in spectra_to_fit])
    mutliplet_results.insert(loc = 1, column = 'proc_no' , value = [int(i[3]) for i in spectra_to_fit])
    mutliplet_results.insert(loc = 2, column = 'row_id' , value = [i[4] for i in spectra_to_fit])

    mutliplet_stats.insert(loc = 0, column = 'exp_no' , value = [i[2] for i in spectra_to_fit])
    mutliplet_stats.insert(loc = 1, column = 'proc_no' , value = [int(i[3]) for i in spectra_to_fit])
    mutliplet_stats.insert(loc = 2, column = 'row_id' , value = [i[4] for i in spectra_to_fit])

    return _multiplet_type_, mutliplet_results, mutliplet_stats

def update_results(mutliplet_results, fname):
    try:
        original_data = pd.read_csv(str(fname), sep="\t")
    except:
        logger.error("Error when opening existing results file.")
    condition = ((original_data['exp_no'].isin(mutliplet_results['exp_no'])) & (original_data['proc_no'].isin(mutliplet_results['proc_no'])) & (original_data['row_id'].isin(mutliplet_results['row_id'])))
    tmp = original_data.loc[[not x for x in condition],:]

    return pd.concat([tmp, mutliplet_results])

def output_txt_file(x_fit,fit_results, stat_results, d_id, scaling_factor,spectra_to_fit,output_path, output_folder,output_name, offset):
    
    cluster_list = getList(d_id)
    for i in cluster_list:
        # create output dataframe
        _multiplet_type_, mutliplet_results, mutliplet_stats = build_output(d_id[i], x_fit, fit_results, stat_results, scaling_factor, spectra_to_fit, offset)
        # update results file if already exists
        fname = Path(output_path,output_folder,output_name+'_'+str(_multiplet_type_)+'_'+str(i)+'_fit.txt')
        sname = Path(output_path,output_folder,output_name+'_'+str(_multiplet_type_)+'_'+str(i)+'_stat.txt')

        pname = Path(output_path,output_folder,output_name+'_'+str(_multiplet_type_)+'_'+str(i)+'_plot_integral.pdf')

        if fname.is_file():
            mutliplet_results = update_results(mutliplet_results, fname)
        if sname.is_file():
            mutliplet_stats = update_results(mutliplet_stats, fname)
        # sort results by exp_no, proc_no & row_id
        mutliplet_results = mutliplet_results.sort_values(['exp_no', 'proc_no', 'row_id'], ascending=(True, True, True))
        mutliplet_stats = mutliplet_stats.sort_values(['exp_no', 'proc_no', 'row_id'], ascending=(True, True, True))

        # plot integrals 

        if mutliplet_results.row_id.is_unique is False:
            x_plot = mutliplet_results.exp_no.tolist()
            plt.xlabel('exp no')
        else:
            x_plot = mutliplet_results.row_id.tolist()
            plt.xlabel('row id')
        plt.plot(x_plot, mutliplet_results.integral,ls='none',marker='o',color='darkblue')
        plt.ylabel('Integral')
        plt.savefig(pname)
        plt.close()
        # save to tsv
        mutliplet_results.to_csv(
            str(fname), 
            index=False, 
            sep = '\t'
            )
        mutliplet_stats.to_csv(
            str(sname), 
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

def save_output_data(user_input, fit_results, stat_results, intensities, x_scale, spectra_to_fit, peak_picking_data, scaling_factor, offset=False, merged_pdf=False):

    output_path         =   user_input['output_path']
    output_folder       =   user_input['output_folder']
    output_name         =   user_input['output_name']

    x_fit = np.linspace(np.min(x_scale),np.max(x_scale),2048)
    d_id = nff.get_fitting_parameters(peak_picking_data, x_fit, scaling_factor)[0]

    fit_results = fit_results.apply(pd.to_numeric)
    Path(output_path,output_folder).mkdir(parents=True,exist_ok=True)

    logger.info('Save data to text file ') 
    output_txt_file(x_fit,fit_results, stat_results, d_id, scaling_factor,spectra_to_fit,output_path, output_folder,output_name, offset)
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
    if merged_pdf:
        merge_pdf(output_path,output_folder,output_name)
    logger.info('Save plot to pdf -- Complete')

