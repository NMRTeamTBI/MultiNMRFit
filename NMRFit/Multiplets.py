# This script contains all the information for mulitplets definition
import numpy as np


def Singlet( x, x0, a, h_s, lw ):
    #Lorentzian + Gaussian    
    S1 = a * h_s  / ( 1 + (( x - x0 )/lw)**2) + (1-a)*h_s*np.exp(-(x-x0)**2/(2*lw**2))    
    Signal = S1
    return Signal * 1e8

def Doublet( x, x0, a, h_s, lw, J1 ):
    #Lorentzian + Gaussian
    S1 = a * h_s  / ( 1 + (( x - x0 - (J1/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - (J1/2))**2/(2*lw**2))
    S2 = a * h_s  / ( 1 + (( x - x0 + (J1/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + (J1/2))**2/(2*lw**2))
    Signal = S1 + S2
    return Signal * 1e8

def DoubletOfDoublet( x, x0, a, h_s, lw, J1, J2):
    #Lorentzian + Gaussian
    S1 = a * h_s  / ( 1 + (( x - x0 - ((J1+J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - ((J1+J2)/2))**2/(2*lw**2))
    S2 = a * h_s  / ( 1 + (( x - x0 - ((J1-J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 - ((J1-J2)/2))**2/(2*lw**2))
    S3 = a * h_s  / ( 1 + (( x - x0 + ((J1+J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + ((J1+J2)/2))**2/(2*lw**2))
    S4 = a * h_s  / ( 1 + (( x - x0 + ((J1-J2)/2))/lw)**2) + (1-a)*h_s*np.exp(-(x - x0 + ((J1-J2)/2))**2/(2*lw**2))
    Signal = S1+S2+S3+S4
    return Signal * 1e8

d_mapping = {
    "Singlet":{"f_function":Singlet,"n_peaks" : 1, "params":['x0','a','Amp','lw'],"n_params" : 4, "constraints":[(1e-6,12),(0.1,1),(1e-6,np.inf),(1e-6,0.5)]},
    "Doublet":{"f_function":Doublet,"n_peaks" : 2,"params":['x0','a','Amp','lw','J1'],"n_params" : 5, "constraints":[(1e-6,12),(1e-6,1),(1e-6,np.inf),(1e-6,1),(2e-3,0.5)]},
    "DoubletofDoublet":{"f_function":DoubletOfDoublet,"n_peaks" : 4,"params":['x0','a','Amp','lw','J1','J2'],"n_params" : 6, "constraints":[(1e-6,12),(1e-6,1),(1e-6,np.inf),(1e-6,1),(2e-3,1),(2e-3,1)]}

    }
d_clustering = {d_mapping[k]["n_peaks"]:k for k in d_mapping.keys()}

d_parameters = {d_mapping[k]["n_params"]:k for k in d_mapping.keys()}

