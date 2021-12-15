import numpy as np
import pandas as pd
from scipy.optimize import minimize


import multinmrfit.multiplets as nmrm

# Set Initial Values for fitting

def Peak_Initialisation(
    Peak_Type='Peak_Type',
    Peak_Picking_Results = 'Peak_Picking_Results',
    scaling_factor=None
    ):
    Line_Width = 0.001
    Ratio_Lorentzian_Gaussian = 0.5

    Peak_Picking_Results[["ppm_H_AXIS", "Peak_Amp"]] = Peak_Picking_Results[["ppm_H_AXIS", "Peak_Amp"]].apply(pd.to_numeric)

    if Peak_Type == 'Singlet':
        Init_Val= [
        Peak_Picking_Results.ppm_H_AXIS.values[0], 
        Ratio_Lorentzian_Gaussian,
        Peak_Picking_Results.Peak_Amp.values[0]/scaling_factor, 
        Line_Width
        ]

    elif Peak_Type =='Doublet':
        x0 = np.mean(Peak_Picking_Results.ppm_H_AXIS)
        J1 = 2*(np.abs(Peak_Picking_Results.ppm_H_AXIS.max())-np.abs(x0))
        Amp = np.mean(Peak_Picking_Results.loc[:,'Peak_Amp'])/scaling_factor

        Init_Val= [
                x0, 
                Ratio_Lorentzian_Gaussian,
                Amp, 
                Line_Width,
                J1
                ]
    #print(Init_Val);exit()
    elif Peak_Type =='DoubletofDoublet':

        x0_init = np.mean(Peak_Picking_Results.loc[:,'ppm_H_AXIS'])
        J_small = Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').ppm_H_AXIS.diff().iloc[1]
        J_large = (np.mean(Peak_Picking_Results.nlargest(2, 'ppm_H_AXIS').ppm_H_AXIS)-np.mean(Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').ppm_H_AXIS))
        Amp_init = np.mean(Peak_Picking_Results.loc[:,'Peak_Amp'])/scaling_factor
        Init_Val= [
                x0_init, 
                Ratio_Lorentzian_Gaussian,
                Amp_init, 
                Line_Width,
                J_small,
                J_large
                ]
    elif Peak_Type =='DoubletofDoubletAsymetric':

        x0_init = np.mean(Peak_Picking_Results.loc[:,'ppm_H_AXIS'])
        J_small = Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').ppm_H_AXIS.diff().iloc[1]
        J_large = (np.mean(Peak_Picking_Results.nlargest(2, 'ppm_H_AXIS').ppm_H_AXIS)-np.mean(Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').ppm_H_AXIS))
        Amp_init = np.mean(Peak_Picking_Results.loc[:,'Peak_Amp'])/scaling_factor
        Init_Val= [
                x0_init, 
                Ratio_Lorentzian_Gaussian,
                Amp_init, 
                Line_Width,
                J_small,
                J_large,
                0
                ]
    elif Peak_Type =='Triplet':
        x0 = np.mean(Peak_Picking_Results.ppm_H_AXIS)
        J1 = (np.abs(Peak_Picking_Results.ppm_H_AXIS.max())-np.abs(x0))
        Amp = Peak_Picking_Results.loc[:,'Peak_Amp'].min()/scaling_factor
        I_ratio = Peak_Picking_Results.loc[:,'Peak_Amp'].max()/Peak_Picking_Results.loc[:,'Peak_Amp'].min()
        Init_Val= [
                x0, 
                Ratio_Lorentzian_Gaussian,
                Amp, 
                Line_Width,
                J1,
                I_ratio
                ]
    else:
        raise ValueError("Peak type is not defined.")
    return Init_Val

def update_resolution(constraints, x_fit_):
    delta = abs(x_fit_[1]-x_fit_[0])
    constraints[3] = (delta, constraints[3][1])
    return constraints

def update_position(constraints, x_fit_):
    constraints[0] = (np.min(x_fit_), np.max(x_fit_))
    return constraints

def Initial_Values(
    peakpicking_data,
    x_fit_,
    scaling_factor
    ):
    ini_params, ini_constraints = [], []
    cluster_list =  peakpicking_data.Cluster.unique()
    d_id = {k:[] for k in cluster_list}
    d_mapping, d_clustering, _ = nmrm.mapping_multiplets()
    Initial_offset = 0
    for n in cluster_list:
        _cluster_ = peakpicking_data.loc[peakpicking_data.Cluster==n]
        id_cluster = str(len(_cluster_)) + "".join(i for i in set(_cluster_.Options.values.tolist()))
        _multiplet_type_ = d_clustering[id_cluster]
        _multiplet_type_function = d_mapping[_multiplet_type_]["f_function"]

        Init_Val = Peak_Initialisation(_multiplet_type_,Peak_Picking_Results=_cluster_,scaling_factor=scaling_factor)
        #Init_Cons = Constraints_Initialisation(_multiplet_type_)
        d_id[n] = (_multiplet_type_function, [len(ini_params),len(ini_params)+len(Init_Val)])
        ini_params.extend(Init_Val)
        upd_cons = update_resolution(d_mapping[_multiplet_type_]["constraints"], x_fit_)
        upd_cons = update_position(d_mapping[_multiplet_type_]["constraints"], x_fit_)
        ini_constraints.extend(upd_cons)
    ini_params.extend([Initial_offset])
    ini_constraints.extend([(-0.1, 0.1)])
    return d_id, ini_params, ini_constraints

def simulate_data(x_fit_, fit_par, d_id, scaling_factor):
    # initialize simulated spectrum at 0
    sim_intensity = np.zeros(len(x_fit_))
    # add subspectrum of each spin system
    for n in d_id.keys():
        # get parameters of spin system
        params = fit_par[d_id[n][1][0]:d_id[n][1][1]]
        # simulate and add corresponding subspectrum
        sim_intensity += d_id[n][0](x_fit_, *params)
    # add offset (corresponds to 0-order baseline correction)
    sim_intensity += fit_par[-1]
    # multiply by scaling factor (required for stable minimization)
    sim_intensity *= scaling_factor
    return sim_intensity

def fit_objective(
    fit_par,
    x_fit_,
    peakpicking_data,
    y_fit_,
    d_id,
    scaling_factor
    ):
    sim_intensity = simulate_data(x_fit_,fit_par, d_id, scaling_factor)
    rmsd = np.sqrt(np.mean((sim_intensity - y_fit_)**2))
    return rmsd

def Fitting_Function(
    x_fit_,
    peakpicking_data,
    y_fit_,
    scaling_factor,
    Initial_Val=None):

    if Initial_Val is not None:        
        init_ = Initial_Val
    else:
        init_=Initial_Values(peakpicking_data, x_fit_, scaling_factor)[1]
    #bounds_fit_ = Initial_Values(peakpicking_data, x_fit_, d_clustering, d_mapping)[2]
    d_id, _, bounds_fit_ = Initial_Values(peakpicking_data, x_fit_, scaling_factor)
    res_fit = minimize(
                fit_objective,
                x0=init_,                
                bounds=bounds_fit_,
                method='L-BFGS-B',
                #options={'ftol': 1e-6},#,'maxiter':0},
                args=(x_fit_,peakpicking_data,y_fit_, d_id, scaling_factor),
    )
    return res_fit

def Pseudo2D_PeakFitting(   
    Intensities =   'Intensities'           ,
    x_Spec      =   'x_Spec'                ,    
    ref_spec    =   'ref_spec'              ,
    peak_picking_data = 'peak_picking_data',
    scaling_factor=None,
    gui=False
    ): 
    if Intensities.ndim == 1:
        n_spec = 1
    else:
        n_spec = Intensities.shape[0]

    id_spec_ref = int(ref_spec)-1
    id_spec_sup = np.arange(id_spec_ref+1,n_spec,1)
    id_spec_inf = np.arange(0,id_spec_ref,1)

    if Intensities.ndim == 1:
        y_Spec_init_ = Intensities
    else:
        y_Spec_init_ = Intensities[id_spec_ref,:]
    #Fitting of the reference 1D spectrum -- This function can be used for 1D spectrum alone
    print('Reference Spectrum Fitting : reference spectrum: '+str(ref_spec))
    Initial_Fit_ = Fitting_Function(
        x_Spec,
        peak_picking_data,
        y_Spec_init_,
        scaling_factor)
    print('Reference Spectrum Fitting -- Complete')
    print('#--------#')
    Fit_results = pd.DataFrame(
        index=np.arange(0,n_spec,1),
        columns=np.arange(0,len(Initial_Fit_.x.tolist()),1)
            )
    if Intensities.ndim == 1:
        Fit_results.loc[0,:] = Initial_Fit_.x.tolist()
    if gui:
        from tqdm.gui import tqdm
        leave=False
    else:
        from tqdm import tqdm
        leave=True
    if Intensities.ndim != 1:
        Fit_results.loc[id_spec_ref,:] = Initial_Fit_.x.tolist()
        if ref_spec != str(n_spec):
            print('Ascending Spectrum Fitting : from: '+str(ref_spec)+' to '+str(np.max(id_spec_sup)))
            for s in tqdm(id_spec_sup, leave=leave):
                y_Spec = Intensities[s,:]
                Initial_Fit_Values = list(Fit_results.loc[s-1].iloc[:].values) #!!!!!!!!!!!!!!!!!!!!!!! config if initial values
                try:
                    _1D_Fit_ = Fitting_Function(
                                x_Spec,
                                peak_picking_data,
                                y_Spec,
                                scaling_factor,
                                Initial_Fit_Values)                   
                    
                    # for n in range(len(Col_Names)-1):
                    Fit_results.loc[s,:] = _1D_Fit_.x.tolist()

                except:
                    print('Error'+str(s))
        print('#--------#')
        if ref_spec != '1':
            print('Descending Spectrum Fitting : from: '+str(np.min(id_spec_inf))+' to '+str(np.max(id_spec_inf)))
            for s in tqdm(id_spec_inf[::-1], leave=leave):
                # print(s,s+1)
                y_Spec = Intensities[s,:]   
                Initial_Fit_Values = list(Fit_results.loc[s+1].iloc[:].values) #!!!!!!!!!!!!!!!!!!!!!!! config if initial values
                try:
                    _1D_Fit_ = Fitting_Function(
                                x_Spec,
                                peak_picking_data,
                                y_Spec,
                                scaling_factor,
                                Initial_Fit_Values) 

                    Fit_results.loc[s,:] = _1D_Fit_.x.tolist()
                except:
                    print('Error'+str(s))
        print('#--------#')
    return Fit_results
