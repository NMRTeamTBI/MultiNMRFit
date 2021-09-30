import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from tqdm import tqdm

from Multiplets import *

# Set Initial Values for fitting
Line_Width = 0.001
Ratio_Lorentzian_Gaussian = 0.5

def Peak_Initialisation(
    Peak_Type='Peak_Type',
    Peak_Picking_Results = 'Peak_Picking_Results'
    ):

    Peak_Picking_Results = Peak_Picking_Results.apply(pd.to_numeric)

    if Peak_Type == 'Singlet':
        Init_Val= [
        Peak_Picking_Results.ppm_H_AXIS.values[0], 
        Ratio_Lorentzian_Gaussian,
        Peak_Picking_Results.Peak_Amp.values[0]/1e8, 
        Line_Width
        ]

    if Peak_Type =='Doublet':
        x0 = np.mean(Peak_Picking_Results.ppm_H_AXIS)
        J1 = 2*(np.abs(Peak_Picking_Results.ppm_H_AXIS.max())-np.abs(x0))
        Amp = np.mean(Peak_Picking_Results.loc[:,'Peak_Amp'])

        Init_Val= [
                x0, 
                Ratio_Lorentzian_Gaussian,
                Amp, 
                Line_Width,
                J1
                ]
    if Peak_Type =='DoubletofDoublet':

        x0_init = np.mean(Peak_Picking_Results.loc[:,'ppm_H_AXIS'])
        J_small = Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').ppm_H_AXIS.diff().iloc[1]
        J_large = (np.mean(Peak_Picking_Results.nlargest(2, 'ppm_H_AXIS').ppm_H_AXIS)-np.mean(Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').ppm_H_AXIS))
        Amp_init = np.mean(Peak_Picking_Results.loc[:,'Peak_Amp'])
        Init_Val= [
                x0_init, 
                Ratio_Lorentzian_Gaussian,
                Amp_init, 
                Line_Width,
                J_small,
                J_large
                ]
    return Init_Val

def Initial_Values(
    peakpicking_data
    ):
    ini_params = []
    cluster_list =  peakpicking_data.Cluster.unique()
    d_id = {k:[] for k in cluster_list}
 
    for n in cluster_list:
        _cluster_ = peakpicking_data.loc[peakpicking_data.Cluster==n]
        _multiplet_type_ = d_clustering[len(_cluster_)]
        _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]

        Init_Val = Peak_Initialisation(_multiplet_type_,Peak_Picking_Results=_cluster_)
        d_id[n] = [len(ini_params),len(ini_params)+len(Init_Val)]
        ini_params.extend(Init_Val)

    return d_id, ini_params

def simulate_data(
    x_fit_,
    peakpicking_data,
    fit_par, 
    ):
    sim_intensity = np.zeros(len(x_fit_))
    cluster_list =  peakpicking_data.Cluster.unique()
    d_id = Initial_Values(peakpicking_data)[0]
    for n in cluster_list:
        _cluster_ = peakpicking_data.loc[peakpicking_data.Cluster==n]
        _multiplet_type_ = d_clustering[len(_cluster_)]
        _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]
        params = fit_par[d_id[n][0]:d_id[n][1]] 
        y = _multiplet_type_function(x_fit_, *params)
        sim_intensity += y

    return sim_intensity  

def fit_objective(
    fit_par,
    x_fit_,
    peakpicking_data,
    y_fit_,
    ):
    sim_intensity = simulate_data(x_fit_,peakpicking_data,fit_par)
    rmsd = np.sqrt(np.mean((sim_intensity - y_fit_)**2))
    return rmsd

def Fitting_Function(
    x_fit_,
    peakpicking_data,
    y_fit_,
    Initial_Val=None):

    if Initial_Val is not None:        
        init_ = Initial_Val
    else:
        init_=Initial_Values(peakpicking_data)[1]
    print(init_)  
    # bounds_fit_ = [ (1e-6,np.inf) for i in range(len(init_))]
    bounds_fit_ = [(1e-6,12),(1e-6,1),(1e-6,np.inf),(1e-6,1)]

    res_fit = minimize(
                fit_objective,
                x0=init_,                
                bounds=bounds_fit_,
                method='L-BFGS-B',
                options={'ftol': 1e-6},#,'maxiter':0},
                args=(x_fit_,peakpicking_data,y_fit_),
    )
    return res_fit

def Pseudo2D_PeakFitting(   
    Intensities =   'Intensities'           ,
    x_Spec      =   'x_Spec'                ,    
    ref_spec    =   'ref_spec'              ,
    peak_picking_data = 'peak_picking_data'
    ): 

    n_spec = Intensities.shape[0]
    ref_spec = int(ref_spec)-1
    spec_sup = np.arange(ref_spec+1,n_spec,1)
    spec_inf = np.arange(0,ref_spec,1)

    y_Spec_init_ = Intensities[ref_spec,:]

    #Fitting of the reference 1D spectrum -- This function can be used for 1D spectrum alone
    Initial_Fit_ = Fitting_Function(
        x_Spec,
        peak_picking_data,
        y_Spec_init_)
 
    Fit_results = pd.DataFrame(
        index=np.arange(0,n_spec,1),
        columns=np.arange(0,len(Initial_Fit_.x.tolist()),1)
            )

    Fit_results.loc[ref_spec,:] = Initial_Fit_.x.tolist()

    for s in tqdm(spec_sup):
    # for s in spec_sup:
        y_Spec = Intensities[s-1,:]
        Initial_Fit_Values = list(Fit_results.loc[s-1].iloc[:].values)
        try:
            _1D_Fit_ = Fitting_Function(
                        x_Spec,
                        peak_picking_data,
                        y_Spec,
                        Initial_Fit_Values)                   
            
            # for n in range(len(Col_Names)-1):
            Fit_results.loc[s,:] = _1D_Fit_.x.tolist()
        except:
            print('Error'+str(s))

    # for s in spec_inf[::-1]:
    for s in tqdm(spec_inf[::-1]):
        # print(s,s+1)
        y_Spec = Intensities[s,:]   
        Initial_Fit_Values = list(Fit_results.loc[s+1].iloc[:].values) 
        try:
            _1D_Fit_ = Fitting_Function(
                        x_Spec,
                        peak_picking_data,
                        y_Spec,
                        Initial_Fit_Values) 

            Fit_results.loc[s,:] = _1D_Fit_.x.tolist()
        except:
            print('Error'+str(s))

    return Fit_results
