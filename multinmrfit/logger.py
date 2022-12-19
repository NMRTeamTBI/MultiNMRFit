"""Logger module containing the MultiNMRFit logger setup"""

import logging

# Setup base logger

mod_logger = logging.getLogger("MultiNMRFit_Logger")
mod_logger.setLevel(logging.DEBUG)


def initialize_fitter_logger(verbose):
    logger = logging.getLogger(f"MultiNMRFit_Logger.base.fitter.SpectrumFitter")
    logger.setLevel(logging.DEBUG)

    return logger
