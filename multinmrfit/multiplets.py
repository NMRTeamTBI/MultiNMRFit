# This script contains all the information for mulitplets definition

import numpy as np
import pandas as pd

def Singlet( x, x0, a, h_s, lw ):
    #Lorentzian + Gaussian    
    S1 = a * h_s  / ( 1 + (( x - x0 )/lw)**2) 
    Signal = S1
    return Signal

def Doublet( x, x0, a, h_s, lw, J1 ):
    #Lorentzian + Gaussian
    S1 = a * h_s  / ( 1 + (( x - x0 - (J1/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - (J1/2))**2/(2*lw**2))
    S2 = a * h_s  / ( 1 + (( x - x0 + (J1/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + (J1/2))**2/(2*lw**2))
    Signal = S1 + S2
    return Signal

def DoubletOfDoublet( x, x0, a, h_s, lw, J1, J2):
    #Lorentzian + Gaussian
    S1 = a * h_s  / ( 1 + (( x - x0 - ((J1+J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - ((J1+J2)/2))**2/(2*lw**2))
    S2 = a * h_s  / ( 1 + (( x - x0 - ((J1-J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - ((J1-J2)/2))**2/(2*lw**2))
    S3 = a * h_s  / ( 1 + (( x - x0 + ((J1+J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + ((J1+J2)/2))**2/(2*lw**2))
    S4 = a * h_s  / ( 1 + (( x - x0 + ((J1-J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + ((J1-J2)/2))**2/(2*lw**2))
    Signal = S1+S2+S3+S4
    return Signal

def DoubletofDoubletAsymetric( x, x0, a, h_s, lw, J1, J2, dH):
    #Lorentzian + Gaussian
    S1 = a * (h_s-dH)  / ( 1 + (( x - x0 - ((J1+J2)/2))/lw)**2) + (1-a)*(h_s-dH)*np.exp(-(x - x0 - ((J1+J2)/2))**2/(2*lw**2))
    S2 = a * (h_s+dH)  / ( 1 + (( x - x0 - ((J1-J2)/2))/lw)**2) + (1-a)*(h_s+dH)*np.exp(-(x - x0 - ((J1-J2)/2))**2/(2*lw**2))
    S3 = a * (h_s-dH)  / ( 1 + (( x - x0 + ((J1+J2)/2))/lw)**2) + (1-a)*(h_s-dH)*np.exp(-(x - x0 + ((J1+J2)/2))**2/(2*lw**2))
    S4 = a * (h_s+dH)  / ( 1 + (( x - x0 + ((J1-J2)/2))/lw)**2) + (1-a)*(h_s+dH)*np.exp(-(x - x0 + ((J1-J2)/2))**2/(2*lw**2))
    Signal = S1+S2+S3+S4
    return Signal

def Triplet( x, x0, a, h_s, lw, J1):
    #Lorentzian + Gaussian
    S1 = a * h_s  / ( 1 + (( x - x0 - J1)/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - J1)**2/(2*lw**2))
    S2 = a * 2* h_s  / ( 1 + (( x - x0 )/lw)**2) + (1-a)*2*h_s*np.exp(-(x - x0 )**2/(2*lw**2))
    S3 = a * h_s  / ( 1 + (( x - x0 + J1)/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + J1)**2/(2*lw**2))
    Signal = S1+S2+S3
    return Signal

def mapping_multiplets(lw_constraints = (1e-3,1e-2), x0_constraints = (1e-6,12), a_constraints = (0.,1.), Amp_constraints = (1e-6,np.inf), dH_constraints= (0, np.inf), J_constraints = (2.5e-3,0.03)):
    d_mapping = {
        "Singlet":{"f_function":Singlet,"n_peaks" : "1", "option":"", "params":['x0','a','Amp','lw'],"n_params" : 4, "constraints":[x0_constraints,a_constraints,Amp_constraints,lw_constraints]},
        "Doublet":{"f_function":Doublet,"n_peaks" : "2", "option":"","params":['x0','a','Amp','lw','J1'],"n_params" : 5, "constraints":[x0_constraints,a_constraints,Amp_constraints,lw_constraints,J_constraints]},
        "DoubletofDoublet":{"f_function":DoubletOfDoublet,"n_peaks" : "4", "option":"","params":['x0','a','Amp','lw','J1','J2'],"n_params" : 6, "constraints":[x0_constraints,a_constraints,Amp_constraints,lw_constraints,J_constraints,J_constraints]},
        "DoubletofDoubletAsymetric":{"f_function":DoubletofDoubletAsymetric,"n_peaks" : "4", "option":"Roof","params":['x0','a','Amp','lw','J1','J2', 'dH'],"n_params" : 7, "constraints":[x0_constraints,a_constraints,Amp_constraints,lw_constraints,J_constraints,J_constraints, dH_constraints]},
        "Triplet":{"f_function":Triplet,"n_peaks" : "3", "option":"","params":['x0','a','Amp','lw','J1'],"n_params" : 5, "constraints":[x0_constraints,a_constraints,Amp_constraints,lw_constraints,J_constraints]},
        }
    #  create d_clustering with 'n_peaks + option' as keys (so must be unique, otherwise construction of this dict must be modified)
    d_clustering = {(d_mapping[k]["n_peaks"]+d_mapping[k]["option"]):k for k in d_mapping.keys()}
    return d_mapping, d_clustering

def Peak_Initialisation(
    Peak_Type='Peak_Type',
    Peak_Picking_Results = 'Peak_Picking_Results',
    scaling_factor=None
    ):
    
    Line_Width = 0.001
    Ratio_Lorentzian_Gaussian = 0.5

    Peak_Picking_Results[["Peak_Position", "Peak_Intensity"]] = Peak_Picking_Results[["Peak_Position", "Peak_Intensity"]].apply(pd.to_numeric)

    if Peak_Type == 'Singlet':
        Init_Val= [
        Peak_Picking_Results.Peak_Position.values[0], 
        Ratio_Lorentzian_Gaussian,
        Peak_Picking_Results.Peak_Intensity.values[0]/scaling_factor, 
        Line_Width
        ]

    elif Peak_Type =='Doublet':
        x0 = np.mean(Peak_Picking_Results.Peak_Position)
        J1 = 2*(np.abs(Peak_Picking_Results.Peak_Position.max())-np.abs(x0))
        Amp = np.mean(Peak_Picking_Results.loc[:,'Peak_Intensity'])/scaling_factor
        Init_Val= [
                x0, 
                Ratio_Lorentzian_Gaussian,
                Amp, 
                Line_Width,
                J1
                ]

    elif Peak_Type =='DoubletofDoublet':
        x0_init = np.mean(Peak_Picking_Results.loc[:,'Peak_Position'])
        J_small = Peak_Picking_Results.nsmallest(2, 'Peak_Position').Peak_Position.diff().iloc[1]
        J_large = (np.mean(Peak_Picking_Results.nlargest(2, 'Peak_Position').Peak_Position)-np.mean(Peak_Picking_Results.nsmallest(2, 'Peak_Position').Peak_Position))
        Amp_init = np.mean(Peak_Picking_Results.loc[:,'Peak_Intensity'])/scaling_factor
        Init_Val= [
                x0_init, 
                Ratio_Lorentzian_Gaussian,
                Amp_init, 
                Line_Width,
                J_small,
                J_large
                ]

    elif Peak_Type =='DoubletofDoubletAsymetric':
        x0_init = np.mean(Peak_Picking_Results.loc[:,'Peak_Position'])
        J_small = Peak_Picking_Results.nsmallest(2, 'Peak_Position').Peak_Position.diff().iloc[1]
        J_large = (np.mean(Peak_Picking_Results.nlargest(2, 'Peak_Position').Peak_Position)-np.mean(Peak_Picking_Results.nsmallest(2, 'Peak_Position').Peak_Position))
        Amp_init = np.mean(Peak_Picking_Results.loc[:,'Peak_Intensity'])/scaling_factor
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
        x0 = np.mean(Peak_Picking_Results.Peak_Position)
        J1 = (np.abs(Peak_Picking_Results.Peak_Position.max())-np.abs(x0))
        Amp = Peak_Picking_Results.loc[:,'Peak_Intensity'].min()/scaling_factor
        Init_Val= [
                x0, 
                Ratio_Lorentzian_Gaussian,
                Amp, 
                Line_Width,
                J1
                ]
    else:
        raise ValueError("Unknown multiplicity provided, please check 'Peak_Type'.")

    return Init_Val

default_constraints = {
    'lw':{'low_bounds':1e-3, 'high_bounds':1e-2, 'relative_window':1e-3, 'info': 'line width (ppm)'},
    'a':{'low_bounds':0, 'high_bounds':1, 'relative_window':1e-3, 'info': 'ratio L/G'},
    'x0':{'low_bounds':1e-6, 'high_bounds':12, 'relative_window':1e-3, 'info': 'peak position (ppm)'},
    'Amp':{'low_bounds':1e-6, 'high_bounds':np.inf, 'relative_window':1e-3, 'info': 'peak amplitude'},
    'J':{'low_bounds':2.5e-3, 'high_bounds':0.03, 'relative_window':1e-3, 'info': 'coupling constant (ppm)'}
    }  
