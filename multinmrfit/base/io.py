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


    def load_data(self, data, window: tuple = None, rowno: int = None):

        # initialize metadata & load NMR data
        if isinstance(data, pd.DataFrame):
            dataset = {"data_path": None,
                       "dataset": None,
                       "expno": None,
                       "procno": None,
                       "rowno": rowno,
                       "window": window}
            dataset["ppm"], dataset["intensity"] = self.filter_window(data.ppm, data.intensity, window)
        elif isinstance(data, dict):
            dataset = data
            dataset["window"] = window
            dataset["ppm"], dataset["intensity"] = self.read_topspin_data(dataset["data_path"], dataset["dataset"], dataset["expno"], dataset["procno"], rowno=dataset.get("rowno", None), window=window)
        else:
            raise TypeError("Data must be provided as a dict or a dataframe.")
        return dataset


    @staticmethod
    def read_topspin_data(data_path, dataset, expno, procno, rowno=None, window=None):

        # get complete data path
        full_path = Path(data_path, dataset, expno, 'pdata', procno)
        # get dimension
        ndim = 1 if rowno is None else 2

        # read processed data
        dic, data = ng.bruker.read_pdata(str(full_path), read_procs=True, read_acqus=False, scale_data=True, all_components=False)

        # extract ppm and intensities
        udic = ng.bruker.guess_udic(dic, data)
        uc_F = ng.fileiobase.uc_from_udic(udic, ndim-1)
        ppm = pd.Series(uc_F.ppm_scale())
        if ndim == 2:
            data = data[int(rowno)]
        intensity = pd.Series(data)

        # filter selected window
        if window is not None:
            mask = (ppm >= window[0]) & (ppm <= window[1])
            ppm = ppm[mask]
            intensity = intensity[mask]

        # reset index
        ppm.reset_index(inplace=True, drop=True)
        intensity.reset_index(inplace=True, drop=True)

        return ppm, intensity


    @staticmethod
    def filter_window(ppm: list, intensity: list, window: tuple = None):

        # filter selected window
        if window is not None:
            mask = (ppm >= window[0]) & (ppm <= window[1])
            ppm = ppm[mask]
            intensity = intensity[mask]

        # reset index
        ppm.reset_index(inplace=True, drop=True)
        intensity.reset_index(inplace=True, drop=True)

        return ppm, intensity

    @staticmethod
    def load_1D_spectrum(data_path, dataset, procno, expno_list):
        ppm_all = []
        data_all = []
        
        for exp in expno_list:

            # get complete data path
            full_path = Path(data_path, dataset, str(exp), 'pdata', procno)
        
            # read processed data
            try:
                dic, data = ng.bruker.read_pdata(str(full_path), read_procs=True, read_acqus=False, scale_data=True, all_components=False)

                # extract ppm and intensities
                udic = ng.bruker.guess_udic(dic, data)
                uc_F = ng.fileiobase.uc_from_udic(udic, 0)
                ppm = uc_F.ppm_scale()
                ppm_all.append(ppm)
                data_all.append([data][0])
            except Exception as e:
                raise ValueError("An unknown error has occurred when opening spectrum: '{}'. Please check your inputs.".format(e))
        
        try:
            data = np.array(data_all)
        except:
            raise ValueError("All spectra do not have the same length.")

        return ppm_all[0], data, expno_list

    @staticmethod
    def load_txt_spectrum(txt_data):
        if "ppm" not in txt_data.columns:
            raise ValueError("Column 'ppm' missing")
        ppm = txt_data.ppm.values.tolist()
        data = np.array(txt_data.loc[:, txt_data.columns != 'ppm']).transpose()
        names = [int(i) for i in txt_data.columns[txt_data.columns != 'ppm'].tolist()]

        return ppm, data, names

    @staticmethod
    def load_2D_spectrum(data_path, dataset, expno, procno):
        """Load 2D NMR spectra.

        Returns:
            list: chemical shift
            list: intensity
        """
        # get complete data path

        full_path = Path(data_path, dataset, expno, 'pdata', procno)
        
        # read processed data
        try:
            dic, data = ng.bruker.read_pdata(str(full_path), read_procs=True, read_acqus=False, scale_data=True, all_components=False)
            # extract ppm and intensities
            udic = ng.bruker.guess_udic(dic, data)
            uc_F = ng.fileiobase.uc_from_udic(udic, 1)
            ppm = pd.Series(uc_F.ppm_scale())
            names = list(range(1, data.shape[0]+1))
        except Exception as e:
            raise ValueError("An unknown error has occurred when opening spectrum: '{}'. Please check your inputs.".format(e))

        return ppm, data, names

    def check_dataset(self):

        if not Path(self.data_path).exists():
            raise ValueError("Directory '{}' does not exist.".format(self.data_path))

        full_path = Path(self.data_path, self.dataset, self.expno, 'pdata', self.procno)

        if not full_path.exists():
            raise ValueError("Directory '{}' does not exist.".format(full_path))
