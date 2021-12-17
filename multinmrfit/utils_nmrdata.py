import numpy as np
import nmrglue as ng
import os

import tkinter as tk
import pandas as pd

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

def Read_Raw_NMR_Data_Bruker(
        path_nmr_data   =   'path_nmr_data',
        expno_data      =   'expno_data',
        procno_data     =   'procno_data',
        ):
    path = os.path.join(path_nmr_data,str(expno_data),'pdata',str(procno_data))
    dic, data = ng.bruker.read_pdata(
        path,
        read_procs=True,
        read_acqus=False,
        scale_data = True,
        all_components=False
        )
    n_dim = len(data.shape) 
    if n_dim == 1:       
        udic = ng.bruker.guess_udic(dic,data)
        uc_F1 = ng.fileiobase.uc_from_udic(udic, 0)
        ppm_scale_F1 = uc_F1.ppm_scale()
        output = [data,dic,ppm_scale_F1]
    if n_dim == 2:
        udic = ng.bruker.guess_udic(dic,data)
        uc_F2 = ng.fileiobase.uc_from_udic(udic, 1)
        ppm_scale_F2 = uc_F2.ppm_scale()
        # Clean data for data stopped before the end!
        data = data[~np.all(data == 0, axis=1)]

        output = (data,dic,ppm_scale_F2)
    return output

def Extract_Data(
    data = 'data',
    x_ppm = 'x_ppm',
    x_lim = 'x_lim'
    ):
    n_dim = len(data.shape) 
    if n_dim == 1:     
        idx_x0_F1, x0_F1 = find_nearest(x_ppm,x_lim[0])
        idx_x1_F1, x1_F1 = find_nearest(x_ppm,x_lim[1])
        data_ext = data[idx_x0_F1:idx_x1_F1]
        x_ppm_ext = x_ppm[idx_x0_F1:idx_x1_F1]
        output = [data_ext, x_ppm_ext]
    if n_dim == 2:
        if x_ppm.ndim == 1:
            idx_x0_F2, x0_F2 = find_nearest(x_ppm,x_lim[0])
            idx_x1_F2, x1_F2 = find_nearest(x_ppm,x_lim[1])
            data_ext = data[:,idx_x0_F2:idx_x1_F2]
            x_ppm_ext = x_ppm[idx_x0_F2:idx_x1_F2]
            output = [data_ext, x_ppm_ext]
        if x_ppm.ndim != 1:
            n_s = x_ppm.shape[0]
            for k in range(n_s):
                idx_x0_F2, x0_F2 = find_nearest(x_ppm[k],x_lim[0])
                idx_x1_F2, x1_F2 = find_nearest(x_ppm[k],x_lim[1])
                if k == 0:
                    data_ext= data[k,idx_x0_F2:idx_x1_F2]
                    x_ppm_ext = x_ppm[k,idx_x0_F2:idx_x1_F2] 
                    dim_spectra = abs(idx_x1_F2-idx_x0_F2)
                else:
                    if abs(idx_x1_F2-idx_x0_F2) < dim_spectra:
                        idx_x0_F2 -= 1
                    elif abs(idx_x1_F2-idx_x0_F2) > dim_spectra:
                        idx_x0_F2 += 1
                    data_ext= np.vstack([data_ext,data[k,idx_x0_F2:idx_x1_F2]])
                    x_ppm_ext= np.vstack([x_ppm_ext,x_ppm[k,idx_x0_F2:idx_x1_F2]])
        output = [data_ext, x_ppm_ext]

    return output

def Peak_Picking_1D(
    x_data          =   'x_data', 
    y_data          =   'y_data', 
    threshold       =   'threshold',
    ):
    
    try: 
        peak_table = ng.peakpick.pick(
            y_data, 
            pthres=threshold, 
            algorithm='downward',
            )
        # Find peak locations in ppm
        peak_locations_ppm = []
        for i in range(len(peak_table['X_AXIS'])):
            pts = int(peak_table['X_AXIS'][i])
            peak_locations_ppm.append(x_data[pts])

        # Find the peak amplitudes
        peak_amplitudes = y_data[peak_table['X_AXIS'].astype('int')]

        results = pd.DataFrame(columns=['ppm_H_AXIS','Peak_Amp'],index=np.arange(1,len(peak_table)+1))
        results.loc[:,'ppm_H_AXIS'] = peak_locations_ppm
        results.loc[:,'Peak_Amp'] = peak_amplitudes
        results = results.sort_values(by='ppm_H_AXIS', ascending=True)
    except:
        main = tk.Tk()
        main.title("Error")
        
        str_var = tk.StringVar()
        #Message Function
        label = tk.Message( main, textvariable=str_var, 
            relief=tk.RAISED,width=400,foreground='red')
        str_var.set("No signal were found \n Lower the threshold") 
        label.pack()
        main.mainloop()
        exit()

    return results

def sort_peak_picking_data(peak_picking_data, n_peak_max):
    if len(peak_picking_data) >= n_peak_max:
        peak_picking_data = peak_picking_data.sort_values(by='Peak_Amp', ascending=False).head(n_peak_max)
        peak_picking_data = peak_picking_data.sort_values(by='ppm_H_AXIS', ascending=True)
    return peak_picking_data