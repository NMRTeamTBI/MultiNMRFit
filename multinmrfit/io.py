# Import system libraries
from pathlib import Path 
import logging

# Import math libraries
import pandas as pd
import numpy as np

# Import plot libraries
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages

# Import our own libraries
import multinmrfit.fitting as nff
import multinmrfit.multiplets as nfm

logger = logging.getLogger()

def getList(dict):
    return [k for k in dict.keys()]

def getIntegral(x_fit, _multiplet_type_, fit_par):
    d_mapping = nfm.mapping_multiplets()[0]
    _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
    y = _multiplet_type_function(x_fit, *fit_par)
    integral = np.sum(y)*(x_fit[1]-x_fit[0])
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

def build_output(d_id_i, x_fit, fit_results, scaling_factor,data_exp_no,spectra_to_fit,analysis_type):
    d_mapping, _, d_parameters = nfm.mapping_multiplets()
    col = range(d_id_i[1][0],d_id_i[1][1])
    _multiplet_type_ = d_parameters[len(col)]

    mutliplet_results = fit_results[fit_results.columns.intersection(col)]
    mutliplet_results.columns = d_mapping[_multiplet_type_]['params']

    mutliplet_results["integral"] = [scaling_factor*getIntegral(x_fit, _multiplet_type_, row.tolist()) for index, row in mutliplet_results.iterrows()]
    mutliplet_results["Amp"] *= scaling_factor

    if analysis_type == 'Pseudo2D':
        mutliplet_results.insert(loc = 0, column = 'exp_no' , value = np.array([data_exp_no]*len(spectra_to_fit)))
        mutliplet_results.insert(loc = 1, column = 'row_id' , value = spectra_to_fit)
    elif analysis_type == '1D_Series':
        mutliplet_results.insert(loc = 0, column = 'exp_no' , value = spectra_to_fit)
        mutliplet_results.insert(loc = 1, column = 'row_id' , value = [1]*len(spectra_to_fit))

    mutliplet_results.set_index('exp_no', inplace=True)
    return _multiplet_type_, mutliplet_results

def update_results(mutliplet_results, fname, analysis_type):
    try:
        if analysis_type == 'Pseudo2D':
            original_data = pd.read_csv(
                str(fname), 
                sep="\t",
                dtype={'row_id':np.int},index_col='row_id'
                )

        elif analysis_type == '1D_Series':
            original_data = pd.read_csv(
                str(fname), 
                sep="\t",
                dtype={'exp_no':np.int},index_col='exp_no'
                )

    except:
        logger.error("error when opening existing reults file")
    print(original_data)
    print(mutliplet_results)
    if analysis_type == 'Pseudo2D':
        mutliplet_results.set_index('row_id')

    original_data.loc[mutliplet_results.index,:] = mutliplet_results[:]

    return original_data

def output_txt_file(x_fit,fit_results, d_id, scaling_factor,data_exp_no,spectra_to_fit,analysis_type,output_path, output_folder,output_name):
    
    cluster_list = getList(d_id)
    #fit_results = fit_results.round(9)
    for i in cluster_list:        
        _multiplet_type_, mutliplet_results = build_output(d_id[i], x_fit, fit_results, scaling_factor,data_exp_no,spectra_to_fit,analysis_type)
        fname = Path(output_path,output_folder,output_name+'_'+str(_multiplet_type_)+'_'+str(i)+'.txt')
        if fname.is_file():
            mutliplet_results = update_results(mutliplet_results, fname, analysis_type)
        mutliplet_results.to_csv(
            str(fname), 
            index=True, 
            sep = '\t'
            )
    logger.info('Save data to text file -- Complete')

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


    x_fit = np.linspace(np.min(x_scale),np.max(x_scale),2048)
    d_id = nff.Initial_Values(Peak_Picking_data, x_fit, scaling_factor)[0]

    fit_results = fit_results.apply(pd.to_numeric)

    Path(output_path,output_folder).mkdir(parents=True,exist_ok=True)

    logger.info('Save data to text file ') 
    output_txt_file(x_fit,fit_results, d_id, scaling_factor,data_exp_no,spectra_to_fit,analysis_type,output_path, output_folder,output_name)
    logger.info('Save data to text file -- Complete')

    logger.info('Save plot to pdf')
    for r in spectra_to_fit:
        i = None 
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

    logger.info('Save plot to pdf -- Complete')