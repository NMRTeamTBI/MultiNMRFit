from pathlib import Path
import pandas as pd
import nmrglue as ng
import numpy as np
import importlib
import os
import multinmrfit
import logging
from itertools import groupby

# create logger
logger = logging.getLogger(__name__)

class IoHandler():
    def __init__(self):
        pass

    def get_dim(self,dataset):
        """
        Estimate the number of rows in the experiment
        
        Returns:
            integer : number of rows
            tuple : dimensions of the data to be fitted
        """
        ppm, data = self.read_topspin_data(dataset["data_path"], dataset["dataset"], dataset["expno"], dataset["procno"])
        n_row = data.shape[0]
        data_shape = data.shape
        return n_row, data_shape

    def get_ppm_Limits(self,dataset):
        """
        Estimate the ppm limits in the experiment
        (minimum of ppm scale, maximim of ppm scale)

        Returns:
            integers : ppm_min, ppm_max 
        """
        ppm, data = self.read_topspin_data(dataset["data_path"], dataset["dataset"], dataset["expno"], dataset["procno"])
        ppm_min = min(ppm)
        ppm_max = max(ppm)
        return ppm_min, ppm_max

    def model_cluster_list(self):
        """
        Estimate the number of peaks per model
        
        Returns:
            dict : models_peak_number
        """
        models_peak_number = self.get_models_peak_number()
        return models_peak_number
    
    def model_cluster_assignment(self,cluster_ids):
        """
        Estimate the number of peaks per model

        Args:
            cluster_ids (pd.DataFrame): cluster ids provided by the user
        Returns:
            dict : models_peak_number
        """
        print('hello')
        model_list = self.get_models_peak_number()
        
        # get list of different possible models with a similar number of peaks
        d = {n:[k for k in model_list.keys() if model_list[k] == n] for n in set(model_list.values())}

        # get cluster ID defined by user and their occurences
        n_cID = cluster_ids.value_counts()[1:]

        # get user defined cluster names
        cluster_names = n_cID.index.values.tolist()

        cluster = {}
        for c in range(len(n_cID)):    
            cluster[cluster_names[c]]= {'n':int(n_cID[c]),'models':list(d[int(n_cID[c])])}
        
        return cluster
        
    def create_models(self,dict):
        models = self.get_models()
        signals = {}
        for idx, key in enumerate(dict):

            cluster_model = dict[key]['model']
            signals[key]={'model':cluster_model}

            cluster_params = models[cluster_model]()._params
            tmp ={}
            for p in cluster_params.par:
                cluster_params[cluster_params.par==p].ini.values[0]
                tmp[p] = {
                'ini':cluster_params[cluster_params.par==p].ini.values[0],
                'lb':cluster_params[cluster_params.par==p].lb.values[0],
                'ub':cluster_params[cluster_params.par==p].ub.values[0],
                                }
                
            signals[key]={
            'model':cluster_model,
            'par':tmp}
            
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
            

        if n_dim == 2:
            udic = ng.bruker.guess_udic(dic,data)
            uc_F2 = ng.fileiobase.uc_from_udic(udic, 1)
            ppm = pd.Series(uc_F2.ppm_scale())
            # Clean data for data stopped before the end!
            data = data[~np.all(data == 0, axis=1)]

        return ppm, data
    
    @staticmethod
    def get_models_peak_number():
        # """
        # Load signal models.
        
        # Returns: dict containing the different model peak numbers, with model.name as keys
        # """

        models = {}
        model_dir = Path(multinmrfit.__file__).parent / "models"

        for file in os.listdir(str(model_dir)):
            if "model_" in file:
                logger.debug("add model from file '{}'".format(file))
                module = importlib.import_module("multinmrfit.models.{}".format(file[:-3]))
                model_class = getattr(module, "SignalModel")
                logger.debug("model name: {}".format(model_class().name))
                # models[model_class().name] = model_class
                models[model_class().name] = model_class().peak_number
        return models

    @staticmethod
    def get_models():
        """
        Load signal models.
        :return: dict containing the different model objects, with model.name as keys
        """

        models = {}
        model_dir = Path(multinmrfit.__file__).parent / "models"

        for file in os.listdir(str(model_dir)):
            if "model_" in file:
                logger.debug("add model from file '{}'".format(file))
                module = importlib.import_module("multinmrfit.models.{}".format(file[:-3]))
                model_class = getattr(module, "SignalModel")
                logger.debug("model name: {}".format(model_class().name))
                models[model_class().name] = model_class

        return models

