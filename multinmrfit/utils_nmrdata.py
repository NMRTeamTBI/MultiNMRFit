import numpy as np
import nmrglue as ng
from pathlib import Path 
import pandas as pd

def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx, array[idx]

def read_nmr_data_bruker(
        path_nmr_data   =   'path_nmr_data',
        expno_data      =   'expno_data',
        procno_data     =   'procno_data',
        ):
    path = Path(path_nmr_data,str(expno_data),'pdata',str(procno_data))
    dic, data = ng.bruker.read_pdata(
        str(path),
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
        output = [data,ppm_scale_F1]
    if n_dim == 2:
        udic = ng.bruker.guess_udic(dic,data)
        uc_F2 = ng.fileiobase.uc_from_udic(udic, 1)
        ppm_scale_F2 = uc_F2.ppm_scale()
        # Clean data for data stopped before the end!
        data = data[~np.all(data == 0, axis=1)]

        output = (data,ppm_scale_F2)
    return output

def Extract_Data(data, x_ppm, x_lim):
    n_dim = len(data.shape)
    if n_dim == 1:     
        idx_x0_F1, x0_F1 = find_nearest(x_ppm,x_lim[0])
        idx_x1_F1, x1_F1 = find_nearest(x_ppm,x_lim[1])
        data_ext = np.vstack([data[idx_x0_F1:idx_x1_F1],])
        x_ppm_ext = np.vstack([x_ppm[idx_x0_F1:idx_x1_F1],])
        
    if n_dim == 2:
        if x_ppm.ndim == 1:
            idx_x0_F2, x0_F2 = find_nearest(x_ppm,x_lim[0])
            idx_x1_F2, x1_F2 = find_nearest(x_ppm,x_lim[1])
            data_ext = data[:,idx_x0_F2:idx_x1_F2]
            x_ppm_ext = x_ppm[idx_x0_F2:idx_x1_F2]
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
    output = data_ext, x_ppm_ext
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

        results = pd.DataFrame(columns=['Peak_Position','Peak_Intensity'],index=np.arange(1,len(peak_table)+1))
        results.loc[:,'Peak_Position'] = peak_locations_ppm
        results.loc[:,'Peak_Intensity'] = peak_amplitudes
        results = results.sort_values(by='Peak_Position', ascending=True)
    except:
        results = pd.DataFrame(columns=['Peak_Position','Peak_Intensity'],index=[])
    
    return results

def sort_peak_picking_data(peak_picking_data, n_peak_max):
    if len(peak_picking_data) >= n_peak_max:
        peak_picking_data = peak_picking_data.sort_values(by='Peak_Intensity', ascending=False).head(n_peak_max)
        peak_picking_data = peak_picking_data.sort_values(by='Peak_Position', ascending=True)
    return peak_picking_data

def filter_multiple_clusters(Res):
    for i,j in enumerate(Res.Cluster):
        cluster_num = j.split(',')
        if len(cluster_num) > 1:
            for k in cluster_num:
                new_pk = {
                    'Peak_Position': Res.iloc[i].Peak_Position,
                    'Peak_Intensity': Res.iloc[i].Peak_Intensity,
                    'Selection': Res.iloc[i].Selection,
                    'Options': Res.iloc[i].Options,
                    'Cluster': k

                    }
                Res = Res.append(new_pk, ignore_index = True)
            Res = Res.drop(Res.index[i])
    return Res

def retrieve_nmr_data(user_input):
    if user_input['analysis_type'] in ['Pseudo2D']:
        [y_intensities_all, x_ppm_all] = read_nmr_data_bruker(
                path_nmr_data   =   str(Path(user_input['data_path'],user_input['data_folder'])),
                expno_data      =   user_input['data_exp_no'][0],
                procno_data     =   user_input['data_proc_no']
        )

    elif user_input['analysis_type'] in ['1D_Series']:
        if len(user_input['data_exp_no']) == 1:
            [y_intensities_all, x_ppm_all] = read_nmr_data_bruker(
                    path_nmr_data   =   str(Path(user_input['data_path'],user_input['data_folder'])),
                    expno_data      =   user_input['data_exp_no'][0],
                    procno_data     =   user_input['data_proc_no']
            )
        else:
            raw_y_data = []
            raw_x_data = []
            for n in  user_input['data_exp_no']:
                [y_intensity, x_ppm] = read_nmr_data_bruker(
                        path_nmr_data   =   str(Path(user_input['data_path'],user_input['data_folder'])),
                        expno_data      =   n,
                        procno_data     =   user_input['data_proc_no']
                )       
                raw_x_data.append(x_ppm)  
                raw_y_data.append(y_intensity)  

            x_ppm_all = np.array(raw_x_data)
            y_intensities_all = np.array(raw_y_data)
    else:
        raise ValueError("Wrong type of experiment in 'Analysis Type' (expected 'Pseudo2D','1D' or '1D_Series', got '{}').".format(user_input['analysis_type']))
    print(y_intensities_all.shape)

    return y_intensities_all, x_ppm_all