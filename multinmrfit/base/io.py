from pathlib import Path
import importlib
import os
import multinmrfit
import logging

# create logger
logger = logging.getLogger(__name__)

class IoHandler:

    def __init__():
        pass

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
