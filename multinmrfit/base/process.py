from pathlib import Path
import pandas as pd
import nmrglue as ng
import numpy as np
import logging
import string
import pickle
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import multinmrfit.base.io as io
import multinmrfit.base.spectrum as spectrum
import copy


# create logger
logger = logging.getLogger(__name__)

class Process(object):
    """This class is responsible for interacting with a set of spectra to process:

        * data loading
        * peak picking
        * model initialization
        * spectrum simulation
        * spectrum fitting
        * sensitivity analysis
        * plotting
    """

    def __init__(self, dataset):
        """Construct the Process object.

        Args:
            dataset (dict): input data, a dict to load the data from Topspin files.
            window (tuple, optional): lower and upper bounds of the window of interest (in ppm) or full spectrum if None. Defaults to None.
        """

        self.io = io.IoHandler()
        
        self.models = self.io.get_models()

        # extract information
        self.analysis_type = dataset["analysis_type"]
        self.data_path = dataset["data_path"]
        self.dataset = dataset["dataset"]
        self.expno = dataset["expno"]
        self.procno = dataset["procno"]
        self.txt_data = dataset["txt_data"]

        # outputs
        self.output_res_path = dataset["output_res_path"]
        self.output_res_folder = dataset["output_res_folder"]
        self.filename = dataset["output_filename"]

        # initialize attributes
        self.current_spectrum = None
        self.results = {}
        self.consolidated_results = None

        # load spectrum
        if self.analysis_type == "pseudo2D":
            self.ppm_full, self.data_full, self.names = self.io.load_2D_spectrum(self.data_path, self.dataset, self.expno, self.procno)
        elif self.analysis_type == "list of 1Ds":
            expno_list = self.build_list(self.expno)
            self.ppm_full, self.data_full, self.names = self.io.load_1D_spectrum(self.data_path, self.dataset, self.procno, expno_list)
        elif self.analysis_type == "txt data":
            self.ppm_full, self.data_full, self.names = self.io.load_txt_spectrum(self.txt_data)
        else:
            raise ValueError(f"Analysis_type '{self.analysis_type}' not implemented yet.")

        # clean if entire rows of 0
        self.clean_empty_rows()
        
        # get dimensions
        self.exp_dim = self.data_full.shape

        # get list of spectra
        self.spectra_list = list(range(0, self.exp_dim[0]))

        # set default window (full spectrum)
        window = (min(self.ppm_full), max(self.ppm_full))

        # create default spectrum
        self.set_current_spectrum(dataset.get("rowno", self.names[0]), window=window)

    def clean_empty_rows(self):
        """ Removes rows filled with 0 
        """
        self.data_full = self.data_full[~np.all(self.data_full == 0, axis=1)]
        self.names = self.names[:self.data_full.shape[0]]
        
        
    def add_region(self):
        self.results[self.current_spectrum.rowno] = self.results.get(self.current_spectrum.rowno, {})
        self.results[self.current_spectrum.rowno][self.current_spectrum.region] = copy.deepcopy(self.current_spectrum)


    def delete_region(self, rowno, region):
        if rowno is None:
            tmp = list(self.results.keys())
            for s in tmp:
                del self.results[s][region]
                if not len(self.results[s]):
                    del self.results[s]
        else:
            del self.results[rowno][region]
            if not len(self.results[rowno]):
                del self.results[rowno]


    def update_pp_threshold(self, pp_threshold):
        """Update peak picking threshold, and detect peaks.

        Args:
            pp_threshold (int | float): threshold value for peak detection.
        """

        if type(pp_threshold) != float:
            raise ValueError(f"Peak picking threshold must be numeric.")

        # update threshold
        self.current_spectrum.peakpicking_threshold = pp_threshold

        # detect peaks
        self.current_spectrum.edited_peak_table = self.current_spectrum.peak_picking(pp_threshold)


    def set_current_spectrum(self, rowno, window):
        """Set reference spectrum.

        Args:
            rowno (int): rowno of the reference spectrum.
            window (tuple, optional): lower and upper bounds of the window of interest (in ppm) or full spectrum if None. Defaults to None.
        """

        region = str(round(window[0], 2)) + " | " + str(round(window[1], 2))

        if self.results.get(rowno, {}).get(region, None) is None:

            # extract reference spectrum
            tmp_data = pd.concat([pd.Series(self.ppm_full), pd.Series(self.data_full[self.names.index(rowno),:])], axis=1)
            tmp_data.columns = ["ppm", "intensity"]

            # create spectrum
            self.current_spectrum = spectrum.Spectrum(data=tmp_data, window=window, rowno=rowno)

            # update pp threshold
            self.update_pp_threshold(max(self.current_spectrum.intensity)/5)
        
        else:

            self.current_spectrum = copy.deepcopy(self.results[rowno][region])


    def model_cluster_assignment(self):
        """Estimate the number of peaks per model

        Returns:
            dict: {cluster_id:{'n':number of peaks,'models'=[list of possible models with that number of peaks]}
        """

        # filtering and removing none assigned rows
        edited_peak_table = self.current_spectrum.edited_peak_table.dropna()
        # Check if some clusters overlap
        mask = edited_peak_table['cID'].str.contains(',')
        # Duplicate rows for overlapping clusters (if any)
        if sum(filter(None, mask)):
            edited_peak_table_dup = edited_peak_table[~mask]
            rows_to_duplicate = edited_peak_table[mask]
            for i in rows_to_duplicate.index:
                ci = rows_to_duplicate['cID'][i].split(",")
                for j in ci:
                    tmp_row = rows_to_duplicate.loc[[i]]
                    tmp_row.loc[i, "cID"] = j
                    edited_peak_table_dup = pd.concat([edited_peak_table_dup, tmp_row])
            edited_peak_table = edited_peak_table_dup
                
        edited_peak_table = edited_peak_table.replace(r'^\s*$', np.nan, regex=True)
        edited_peak_table.dropna(axis=0, inplace=True)

        model_list = self.get_models_peak_number()

        # get list of different possible models with a similar number of peaks
        d = {n:[k for k in model_list.keys() if model_list[k] == n] for n in set(model_list.values())}

        # # get cluster ID defined by user and their occurences
        n_cID = edited_peak_table.cID.value_counts()

        # get user defined cluster names
        cluster_names = n_cID.index.values.tolist()
        
        clusters_and_models = {}
        for c in range(len(n_cID)):    
            clusters_and_models[cluster_names[c]] = {'n':int(n_cID.iloc[c]), 'models':list(d[int(n_cID.iloc[c])])}
        
        self.current_spectrum._edited_peak_table = edited_peak_table
        
        return clusters_and_models
        

    def create_signals(self, cluster_dict, offset=None):
        """Build model for spectrum fitting.

        Args:
            cluster_dict (dict): dictionary containing peaks assignment.
            offset (dict, optional): add an offset. Defaults to None.
        """

        # initialize signals
        signals = {}
 
        # create signals
        for key in cluster_dict:
            model = self.models[cluster_dict[key]['model']]()
            filtered_peak_table = self.current_spectrum._edited_peak_table[self.current_spectrum._edited_peak_table.cID==key]
            signals[key] = model.pplist2signal(filtered_peak_table)

        self.signals = signals

        # build model
        self.current_spectrum.build_model(signals=self.signals, available_models=self.models, offset=offset)


    def get_models_peak_number(self):
        """Load signal models.

        Returns:
            dict: model peak numbers, with model.name as keys
        """
        
        models_peak_number = {}

        for m in self.models:
            models_peak_number[m] = self.models[m]().peak_number
 
        return models_peak_number


    def update_params(self, params, spectrum=None, region=None):
        """Update parameter.

        Args:
            params (pd.DataFrame): values of new parameters, with same format as Spectrum.params.
            spectrum (optional, int): rowno of the spectrum to update, reference spectrum if None. Default to None.
        """

        # build dictionary from dataframe to update parameters
        pars = {}
        offset = None
        for s in params.index:
            signal_id = params['signal_id'][s]
            if signal_id == "full_spectrum":
                offset = {"ini":params["ini"][s], "ub":params["ub"][s], "lb":params["lb"][s]}
            else:
                par = params['par'][s]
                pars[signal_id] = pars.get(signal_id, {"par":{}})
                pars[signal_id]["par"][par] = pars[signal_id]["par"].get(par, {})
                for k in ["ini", "lb", "ub"]:
                    pars[signal_id]["par"][par][k] = params[k][s]
        
        # update parameters
        if spectrum is None:
            self.current_spectrum.update_params(pars)
            self.current_spectrum.update_offset(offset)
        else:
            self.results[spectrum][region].update_params(pars)
            self.results[spectrum][region].update_offset(offset)
    

    @staticmethod
    def build_list(user_input):
        # check for allowed characters
        allowed = set(string.digits + ',' + '-')
        if not set(user_input) <= allowed:
            return []
        
        # create list
        experiment_list = []
        try:
            for i in user_input.split(','):
                if "-" in i:
                    spectra = i.split('-')
                    if int(spectra[0]) <= int(spectra[1]):
                        experiment_list += range(int(spectra[0]), int(spectra[1])+1)
                    else:
                        experiment_list += range(int(spectra[1]), int(spectra[0])+1)
                else:
                    experiment_list.append(int(i))
        except:
            return []
        return experiment_list


    def build_spectra_list(self, user_input, ref, region, reprocess=True):
        """Build list of spectra.

        Args:
            user_input (str): string to parse.

        Returns:
            list: list of spectra
        """
        experiment_list = self.build_list(user_input)
        
        experiment_list = [i for i in experiment_list if i in self.names]
        exclude = [ref] if reprocess else [k for k in self.results.keys() if region in list(self.results[k].keys())] + [ref]
        experiment_list = [i for i in experiment_list if i not in exclude]

        return experiment_list
    

    def regions(self, rowno=None):

        # get regions
        if rowno is None:
            regions = []
            for _, r in self.results.items():
                regions += list(r.keys())
        else:
            regions = list(self.results.get(rowno, {}).keys())
        
        # remove duplicates
        regions = list(set(regions))

        # sort
        if regions is not None:
            regions.sort()

        return regions


    def compounds(self, rowno=None, region=None):

        # get regions
        compounds = []
        if rowno is None:
            for r in self.results.values():
                if region is None:
                    for s in r.values():
                        compounds += s.params.signal_id.values.tolist()
                else:
                    if region in r.keys():
                        compounds += r[region].params.signal_id.values.tolist()
        else:
            if region is None:
                for s in self.results[rowno].values():
                    compounds += s.params.signal_id.values.tolist() 
            else:
                compounds = self.results[rowno][region].params.signal_id.values.tolist()

        # remove duplicates
        compounds = list(set(compounds))

        # sort
        if compounds is not None:
            compounds.sort()

        return compounds


    def spectra(self, region=None):

        # get spectra
        if region is None:
            spectra = list(self.results.keys())
        else:
            spectra = [k for k in self.results.keys() if region in self.results[k].keys()]
        
        # sort
        if spectra is not None:
            spectra.sort()

        return spectra


    @staticmethod
    def update_bounds(params):
        """Update bounds of parameters.

        Args:
            params (pd.DataFrame): parameters, with same format as Spectrum.params.
        """

        # get current interval between bounds
        interval = (params["ub"] - params["lb"])/2

        # set initial values from best fit of ref spectrum
        params["ini"] = params['opt']

        # shift upper bound
        upper_bounds = params["opt"] + interval
        mask = params['par'].isin(["gl"])
        upper_bounds[mask] = 1.0
        mask = params['par'].isin(["intensity"])
        upper_bounds[mask] = 20 * params["opt"][mask]
        params["ub"] = upper_bounds
        
        # shift lower bound (with some fixed at zero)
        lower_bounds = params["opt"] - interval
        mask = params['par'].isin(['lw']) & (lower_bounds < 0.0)
        lower_bounds[mask] = 0
        mask = params['par'].isin(['gl'])
        lower_bounds[mask] = 0
        mask = params['par'].isin(['intensity'])
        lower_bounds[mask] = 1
        params["lb"] = lower_bounds
        return params


    def fit_from_ref(self, rowno, region, ref, update_pars_from_previous=True):
        """Fit a spectrum using another spectrum as reference.

        Args:
            rowno (int): rowno of the spectrum to fit.
            ref (int): rowno of the spectrum used as reference.
        """

        # create spectrum
        tmp_data = pd.concat([pd.Series(self.ppm_full), pd.Series(self.data_full[self.names.index(rowno),:])], axis=1)
        tmp_data.columns = ["ppm", "intensity"]
        sp = spectrum.Spectrum(data=tmp_data, window=self.results[ref][region].window, from_ref=ref, rowno=rowno)

        # build model
        offset = {} if self.results[ref][region].offset else None
        sp.build_model(signals=self.results[ref][region].signals,
                       available_models=self.models,
                       offset=offset)

        # save spectrum
        self.results[rowno] = self.results.get(rowno, {})
        self.results[rowno][region] = sp

        # get params from previous spectrum
        prev_params = self.results[ref][region].params.copy(deep=True)

        # update bounds
        if update_pars_from_previous:
            prev_params = self.update_bounds(prev_params)

        # update params in spectrum
        self.update_params(prev_params, spectrum=rowno, region=region)

        # fit
        self.results[rowno][region].fit()
        
    def save_process_to_file(self):

        output_path = Path(self.output_res_path, self.output_res_folder)
        output_file_tmp = Path(output_path, self.filename + "_tmp.pkl")
        output_file = Path(output_path, self.filename + ".pkl")

        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_file_tmp, 'wb') as file:
                pickle.dump(self, file)
            output_file.unlink(missing_ok=True)
            output_file_tmp.rename(output_file)
        except Exception as e:
            raise ValueError(f"An unknown error has occured when saving the process file: {e}")


    def consolidate_results(self):
        consolidated_results = []
        for spec in self.results.keys():
            for reg in self.results[spec].keys():
            # all params except integral
                for i in range(len(self.results[spec][reg].params)):
                    tmp = [
                        spec,
                        reg,
                        self.results[spec][reg].params.iloc[i].loc['signal_id'],
                        self.results[spec][reg].params.iloc[i].loc['model'],
                        self.results[spec][reg].params.iloc[i].loc['par'],
                        self.results[spec][reg].params.iloc[i].loc['opt'] if 'opt' in self.results[spec][reg].params.columns else None,
                        self.results[spec][reg].params.iloc[i].loc['opt_sd'] if 'opt' in self.results[spec][reg].params.columns else None,
                    ]
                    consolidated_results.append(tmp)
                
                # add integral rows
                if "integral" in self.results[spec][reg].params.columns:
                    df_integral = self.results[spec][reg].params.loc[:,['signal_id','model','integral']].drop_duplicates()
                    for i in range(len(df_integral)):
                        tmp = [
                            spec,
                            reg,
                            df_integral.signal_id.iloc[i],
                            df_integral.model.iloc[i],
                            'integral',
                            df_integral.integral.iloc[i],
                            0
                        ]
                        consolidated_results.append(tmp)
        self.consolidated_results = pd.DataFrame(consolidated_results,columns = ['rowno','region','signal_id','model','par','opt','opt_sd'])
        self.consolidated_results.sort_values(by=['rowno'],inplace=True)

    def get_current_intensity(self, ppm):
        idx = min(range(len(self.current_spectrum.ppm)), key=lambda i: abs(self.current_spectrum.ppm[i]-ppm))
        return self.current_spectrum.intensity[idx]


    def select_params(self,signal,parameter):
        selected_params = self.consolidated_results[(self.consolidated_results.signal_id==signal)&(self.consolidated_results.par==parameter)]
        return selected_params 
    

    def save_consolidated_results(self,data=False,partial_filename=False):
        output_path = Path(self.output_res_path, self.output_res_folder)
        output_file = Path(output_path, self.filename + ".txt")
        if partial_filename:
             output_file = Path(output_path, partial_filename + ".txt")
        
        if data is not False:
            data.to_csv(output_file,sep='\t', index=False)
        else:
            self.consolidated_results.to_csv(output_file,sep='\t', index=False)

    def save_spetrum_data(self,spectrum, region, filename):
            
        spectrum_to_save = pd.DataFrame(columns=['spectrum','region','ppm','intensity','best_fit'])
        
        spectrum_to_save['ppm'] = self.results[spectrum][region].ppm
        spectrum_to_save['intensity'] = self.results[spectrum][region].intensity
        spectrum_to_save['best_fit'] = self.results[spectrum][region].fit_results.best_fit
        spectrum_to_save['spectrum'] = spectrum
        spectrum_to_save['region'] = region

        for name,model in self.results[spectrum][region].models.items():
           
            spectrum_to_save[str(name)] = model.simulate(
                [self.results[spectrum][region].params['opt'].values.tolist()[i] for i in model._par_idx], 
                self.results[spectrum][region].ppm)

        output_path = Path(self.output_res_path, self.output_res_folder)
        output_file = Path(output_path, filename + ".txt")

        spectrum_to_save.to_csv(output_file,sep='\t', index=False)

    def plot(self, signal, parameter) -> go.Figure:
        selected_params = self.select_params(signal, parameter)
        fig_full = make_subplots(rows=1, cols=1)
        fig_exp = go.Scatter(
            x=selected_params.rowno, 
            y=selected_params.opt, 
            error_y=dict(type='data',array=selected_params.opt_sd),
            mode='markers', 
            name='exp. spectrum', 
            marker_color="#386CB0")
        fig_full.add_trace(fig_exp, row=1, col=1)
        fig_full.update_layout(
            plot_bgcolor="white", 
            xaxis=dict(linecolor="black", mirror=True, showline=True), 
            yaxis=dict(linecolor="black", mirror=True, showline=True, title=parameter),
            legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        return fig_full
    

    @staticmethod
    def highlighter(x):
        # initialize default colors
        color_codes = pd.DataFrame('', index=x.index, columns=x.columns)
        # set Check color to red if opt is close to bounds
        color_codes['opt'] = np.where((x['opt'] < x['lb']*1.05) | (x['opt'] > x['ub']*0.95), 'color:red', None)
        return color_codes

