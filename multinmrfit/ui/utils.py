from pathlib import Path
import pandas as pd
import nmrglue as ng
import numpy as np
import importlib
import os
import multinmrfit
import logging
from itertools import groupby
import multinmrfit.base.io as io
import multinmrfit.base.spectrum as spectrum


# create logger
logger = logging.getLogger(__name__)

class UtilsHandler():
    def __init__(self):
        pass

    def get_dim(self, dataset):
        """
        Estimate the number of rows in the experiment
        
        Returns:
            integer: number of rows
            tuple: dimensions of the data to be fitted
        """

        _, data = self.read_topspin_data(dataset["data_path"], dataset["dataset"], dataset["expno"], dataset["procno"])
        n_row = data.shape[0]
        data_shape = data.shape

        return n_row, data_shape

    def get_ppm_Limits(self,dataset):
        """
        Estimate the ppm limits in the experiment
        (minimum of ppm scale, maximim of ppm scale)

        Returns:
            float: ppm_min
            float: ppm_max
        """

        ppm, _ = self.read_topspin_data(dataset["data_path"], dataset["dataset"], dataset["expno"], dataset["procno"])

        return min(ppm), max(ppm)

    # instead of using this function, call directly self.get_models_peak_number()
    #def model_cluster_list(self):
    #    """
    #    Estimate the number of peaks per model
    #    
    #    Returns:
    #        dict: models_peak_number
    #    """
    #
    #    models_peak_number = self.get_models_peak_number()
    #
    #    return models_peak_number
    
    def model_cluster_assignment(self,edited_peak_table):
        """
        Estimate the number of peaks per model

        Args:
            edited_peak_table (pd.DataFrame)
        Returns:
            dict: {cluster_id:{'n':number of peaks,'models'=[list of possible models with that number of peaks]}
        """

        # filtering and removing none assigned rows
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
            clusters_and_models[cluster_names[c]] = {'n':int(n_cID[c]), 'models':list(d[int(n_cID[c])])}
        
        return clusters_and_models
        
    def create_signals(self, cluster_dict, edited_peak_table):

        models = io.IoHandler.get_models()
        signals = {}
 
        for key in cluster_dict:
            model = models[cluster_dict[key]['model']]()
            filtered_peak_table = edited_peak_table[edited_peak_table.cID==key]
            signals[key] = model.pplist2signal(filtered_peak_table)
      
        return signals

    @staticmethod
    def read_topspin_data(data_path, dataset, expno, procno):

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
    
    @staticmethod # To check
    def get_models_peak_number():
        # """
        # Load signal models.
        #
        # Returns: dict containing the different model peak numbers, with model.name as keys
        # """
        
        models_peak_number = {}
        models = io.IoHandler.get_models()
        for m in models:
            models_peak_number[m] = models[m]().peak_number
 
        return models_peak_number

    @staticmethod
    def fit_from_ref(ref_spectrum, dataset, signals, list_of_spectra):

        utils = utils.UtilsHandler()

        available_models = io.IoHandler.get_models()

        results = [ref_spectrum]

        list_spectra_part1 = sorted([i for i in list_of_spectra if i > ref_spectrum.rowno])
        list_spectra_part2 = sorted([i for i in list_of_spectra if i < ref_spectrum.rowno])

        for i, rowno in enumerate(list_spectra_part1):

            # update dataset
            current_dataset = dataset
            current_dataset["rowno"] = rowno

            # create spectrum object, and build the corresponding model
            sp = spectrum.Spectrum(data=dataset, window=results[i].window)
            sp.build_model(signals=signals, available_models=available_models, offset=results[i].offset)

            # update params from previous spectrum
            sp.params.update(results[i].params)
            # update bounds
            # TODO

            # fit
            sp.fit()

            # save results
            results.append(sp)

        return results
