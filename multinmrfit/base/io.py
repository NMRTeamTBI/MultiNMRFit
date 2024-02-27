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

