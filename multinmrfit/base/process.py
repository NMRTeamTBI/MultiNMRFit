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

    def __init__(self, dataset, window=None):
        """Construct the Process object.

        Args:
            dataset (dict): input data, a dict to load the data from Topspin files.
            window (tuple, optional): lower and upper bounds of the window of interest (in ppm) or full spectrum if None. Defaults to None.
        """

        self.models = io.IoHandler.get_models()

        # extract information
        self.data_path = dataset["data_path"]
        self.dataset = dataset["dataset"]
        self.expno = dataset["expno"]
        self.procno = dataset["procno"]
        self.analysis_type = dataset["analysis_type"]
        self.ref_spectrum_rowno = dataset.get("rowno", 1)
        self.window = window
        self.ppm = None

        # outputs
        self.output_res_path = dataset["output_res_path"]
        self.output_res_folder = dataset["output_res_folder"]
        self.filename = dataset["output_filename"]

        # initialize attributes
        self.ref_spectrum = None
        self.ppm_limits = None
        self.edited_peak_table = None
        self.user_models = {}
        self.peakpicking_threshold = None
        self.signals = None
        self.results = {}
        self.consolidated_results = None

        # get dimensions
        self.exp_dim = self.get_dim()

        # get list of spectra
        self.spectra_list = list(range(1, self.exp_dim[0]+1))
        
        if self.analysis_type == 'txt data':
            print(self.analysis_type)
        else:
            # load spectrum
            self.ppm_full, self.data_full = self.load_2D_spectrum()
            self.set_ref_spectrum(self.ref_spectrum_rowno, window=window)


    def check_dataset(self):

        if not Path(self.data_path).exists():
            raise ValueError("Directory '{}' does not exist.".format(self.data_path))

        full_path = Path(self.data_path, self.dataset, self.expno, 'pdata', self.procno)

        if not full_path.exists():
            raise ValueError("Directory '{}' does not exist.".format(full_path))


    def update_pp_threshold(self, pp_threshold):
        """Update peak picking threshold, and detect peaks.

        Args:
            pp_threshold (int | float): threshold value for peak detection.
        """

        if type(pp_threshold) != float:
            raise ValueError(f"Peak picking threshold must be numeric.")

        # update threshold
        self.peakpicking_threshold = pp_threshold

        # detect peaks
        self.edited_peak_table = self.ref_spectrum.peak_picking(pp_threshold)


    def set_ref_spectrum(self, rowno, window=None):
        """Set reference spectrum.

        Args:
            rowno (int): rowno of the reference spectrum.
            window (tuple, optional): lower and upper bounds of the window of interest (in ppm) or full spectrum if None. Defaults to None.
        """

        # extract reference spectrum
        self.ref_spectrum_rowno = int(rowno)
        tmp_data = pd.concat([pd.Series(self.ppm_full), pd.Series(self.data_full[int(self.ref_spectrum_rowno)-1])], axis=1)
        tmp_data.columns = ["ppm", "intensity"]

        # update window
        if window is not None:
            self.window = window
        
        # create spectrum
        self.ref_spectrum = spectrum.Spectrum(data=tmp_data, window=window)

        # update chemical shifts
        self.ppm = self.ref_spectrum.ppm

        # get ppm limits
        self.ppm_limits = (min(self.ppm), max(self.ppm))

        # update pp threshold
        self.update_pp_threshold(max(self.ref_spectrum.intensity)/5)
        

    def load_2D_spectrum(self):
        """Load 2D NMR spectra.

        Returns:
            list: chemical shift
            list: intensity
        """

        # get complete data path
        full_path = Path(self.data_path, self.dataset, self.expno, 'pdata', self.procno)
        
        # read processed data
        try:
            dic, data = ng.bruker.read_pdata(str(full_path), read_procs=True, read_acqus=False, scale_data=True, all_components=False)

            # extract ppm and intensities
            udic = ng.bruker.guess_udic(dic, data)
            uc_F = ng.fileiobase.uc_from_udic(udic, 1)
            ppm = pd.Series(uc_F.ppm_scale())
        except Exception as e:
            raise ValueError("An unknown error has occurred when opening spectrum: '{}'.".format(e))

        return ppm, data


    def get_dim(self):
        """Estimate the number of rows in the experiment.
        
        Returns:
            tuple: dimensions of the spectrum (colno, rowno)
        """

        _, data = self.read_topspin_data(self.data_path, self.dataset, self.expno, self.procno)

        return data.shape


    def get_ppm_limits(self):
        """Estimate the ppm limits in the experiment (minimum of ppm scale, maximim of ppm scale).
        """

        ppm, _ = self.read_topspin_data(self.data_path, self.dataset, self.expno, self.procno)
        self.ppm_limits = (min(ppm), max(ppm))


    def model_cluster_assignment(self):
        """Estimate the number of peaks per model

        Returns:
            dict: {cluster_id:{'n':number of peaks,'models'=[list of possible models with that number of peaks]}
        """

        # filtering and removing none assigned rows
        edited_peak_table = self.edited_peak_table.replace(r'^\s*$', np.nan, regex=True)
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
            filtered_peak_table = self.edited_peak_table[self.edited_peak_table.cID==key]
            signals[key] = model.pplist2signal(filtered_peak_table)

        self.signals = signals

        # build model
        self.ref_spectrum.build_model(signals=self.signals, available_models=self.models, offset=offset)


    def fit_reference_spectrum(self):
        """Fit reference spectrum.
        """

        # fit reference spectrum
        self.ref_spectrum.fit()

        # add from_ref attribute
        self.ref_spectrum.from_ref = None

        # save in results
        self.results[self.ref_spectrum_rowno] = self.ref_spectrum


    @staticmethod
    def read_topspin_data(data_path, dataset, expno, procno):
        """Load 2D NMR spectra.

        Returns:
            list: chemical shift
            list: intensity
        """

        # Cyril's version ####
        # Complete data path
        full_path = Path(data_path, dataset, expno, 'pdata', procno)
        # # get dimension
        # ndim = 1 if rowno is None else 2

        # # read processed data
        dic, data = ng.bruker.read_pdata(str(full_path), read_procs=True, read_acqus=False, scale_data=True, all_components=False)

        n_dim = len(data.shape) 

        if n_dim == 1:       
            udic = ng.bruker.guess_udic(dic,data)
            uc_F1 = ng.fileiobase.uc_from_udic(udic, 0)
            ppm = pd.Series(uc_F1.ppm_scale())
        elif n_dim == 2:
            udic = ng.bruker.guess_udic(dic,data)
            uc_F2 = ng.fileiobase.uc_from_udic(udic, 1)
            ppm = pd.Series(uc_F2.ppm_scale())
            # Clean data when acquisition has been stopped before the end
            data = data[~np.all(data == 0, axis=1)]

        return ppm, data
    

    def get_models_peak_number(self):
        """Load signal models.

        Returns:
            dict: model peak numbers, with model.name as keys
        """
        
        models_peak_number = {}

        for m in self.models:
            models_peak_number[m] = self.models[m]().peak_number
 
        return models_peak_number


    def update_params(self, params, spectrum=None):
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
            self.ref_spectrum.update_params(pars)
            self.ref_spectrum.update_offset(offset)
        else:
            self.results[spectrum].update_params(pars)
            self.results[spectrum].update_offset(offset)
    

    def build_spectra_list(self, user_input, ref, reprocess=True):
        """Build list of spectra.

        Args:
            user_input (str): string to parse.

        Returns:
            list: list of spectra
        """

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
        
        exclude = [ref] if reprocess else list(self.results.keys()) + [ref]
        experiment_list = [i for i in experiment_list if i not in exclude]

        return experiment_list


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
        mask = params['par'].isin(["gl"]) & (upper_bounds > 1.0)
        upper_bounds[mask] = 1.0
        params["ub"] = upper_bounds
        
        # shift lower bound (with some fixed at zero)
        lower_bounds = params["opt"] - interval
        mask = params['par'].isin(["gl",'lw']) & (lower_bounds < 0.0)
        lower_bounds[mask] = 0
        #mask = params['par'].isin(["lw"]) & (lower_bounds < 0.0)
        #lower_bounds[mask] = 0
        params["lb"] = lower_bounds

        return params


    def fit_from_ref(self, rowno, ref):
        """Fit a spectrum using another spectrum as reference.

        Args:
            rowno (int): rowno of the spectrum to fit.
            ref (int): rowno of the spectrum used as reference.
        """

        # create spectrum
        tmp_data = pd.concat([pd.Series(self.ppm_full), pd.Series(self.data_full[int(rowno)-1])], axis=1)
        tmp_data.columns = ["ppm", "intensity"]
        sp = spectrum.Spectrum(data=tmp_data, window=self.window)

        # build model
        offset = {} if self.results[ref].offset else None
        sp.build_model(signals=self.signals, available_models=self.models, offset=offset)

        # add from_ref attribute
        sp.from_ref = ref

        # save spectrum
        self.results[rowno] = sp

        # get params from previous spectrum
        prev_params = self.results[ref].params.copy(deep=True)

        # update bounds
        prev_params = self.update_bounds(prev_params)

        # update params in spectrum
        self.update_params(prev_params, spectrum=rowno)

        # fit
        self.results[rowno].fit()
        
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
        for j in self.results.keys():
            # all params except integral
            for i in range(len(self.results[j].params)):
                tmp = [
                    j,
                    self.results[j].params.iloc[i].loc['signal_id'],
                    self.results[j].params.iloc[i].loc['model'],
                    self.results[j].params.iloc[i].loc['par'],
                    self.results[j].params.iloc[i].loc['opt'],
                    self.results[j].params.iloc[i].loc['opt_sd'],
                ]
                consolidated_results.append(tmp)
            
            # add integral rows
            df_integral = self.results[j].params.loc[:,['signal_id','model','integral']].drop_duplicates()
            for i in range(len(df_integral)):
                tmp = [
                    j,
                    df_integral.signal_id.iloc[i],
                    df_integral.model.iloc[i],
                    'integral',
                    df_integral.integral.iloc[i],
                    0
                ]
                consolidated_results.append(tmp)
        self.consolidated_results =  pd.DataFrame(consolidated_results,columns = ['rowno','signal_id','model','par','opt','opt_sd'])

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



