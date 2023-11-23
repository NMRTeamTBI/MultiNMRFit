from pathlib import Path
import pandas as pd
import nmrglue as ng
import numpy as np
import importlib
import os
import multinmrfit
import logging

# create logger
logger = logging.getLogger(__name__)

class IoHandler():
    def __init__(self):
        pass

    def get_dim(self,dataset):
        """Estimate the number of rows in the experiment"""
        ppm, data = self.read_topspin_data(dataset["data_path"], dataset["dataset"], dataset["expno"], dataset["procno"])
        n_row = data.shape[0]
        data_shape = data.shape
        return n_row, data_shape

    def get_ppm_Limits(self,dataset):
        """Estimate the ppm limits in the experiment"""
        ppm, data = self.read_topspin_data(dataset["data_path"], dataset["dataset"], dataset["expno"], dataset["procno"])
        ppm_min = min(ppm)
        ppm_max = max(ppm)
        return ppm_min, ppm_max

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


