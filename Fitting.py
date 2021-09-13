import numpy as np
import pandas as pd

# Set Initial Values for fitting
Line_Width = 0.002
Ratio_Lorentzian_Gaussian = 0.5

def Peak_Initialisation(
    Peak_Type='Peak_Type',
    Peak_Picking_Results = 'Peak_Picking_Results'
    ):

    Peak_Picking_Results = Peak_Picking_Results.apply(pd.to_numeric)

    if Peak_Type == 'Singlet':
        Init_Val= [
        Peak_Picking_Results.ppm_H_AXIS.values[0], 
        0.5,
        Peak_Picking_Results.Peak_Amp.values[0], 
        Line_Width
        ]

    if Peak_Type =='Doublet':
        x0 = np.mean(Peak_Picking_Results.loc[:,'ppm_H_AXIS'])
        J1 = 2*(np.abs(Peak_Picking_Results.loc[2,'ppm_H_AXIS'])-np.abs(x0))
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
        J_small = Peak_Picking_Results.nsmallest(2, 'ppm_H_AXIS').diff(axis=0).ppm_H_AXIS.iloc[1]

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


def simulate_data(
    x_fit_,
    peakpicking_data,
    fit_par, 
    ):

    sim_intensity = np.zeros(len(x_fit_))
    cluster_list =  peakpicking_data.Cluster.unique()
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
    y_Spec,
    ):
    sim_intensity = simulate_data(x_fit_,peakpicking_data,fit_par)
    rmsd = np.sqrt(np.mean((sim_intensity - y_Spec)**2))
    return rmsd
