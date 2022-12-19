"""Logger module containing the MultiNMRFit logger setup"""

import logging

# Setup base logger

mod_logger = logging.getLogger("multinmrfit_logger")
mod_logger.setLevel(logging.DEBUG)


def initialize_fitter_logger(verbose):
    logger = logging.getLogger(f"multinmrfit_logger.base.fitter.Spectrum")
    logger.setLevel(logging.DEBUG)

    return logger
