import logging
import multinmrfit.base.spectrum as spectrum
import multinmrfit.base.io as io
import pandas as pd


# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
strm_hdlr = logging.StreamHandler()
strm_hdlr.setFormatter(formatter)
logger.addHandler(strm_hdlr)

# load available models
available_models = io.IoHandler.get_models()

# data can be provided directly as a pandas dataframe or be loaded from TopSpin files
test_synthetic_dataset = pd.read_table("./data/data_sim_nmrfit.csv", sep="\t")

test_topspin_dataset = {"data_path":"C:/Bruker/TopSpin4.0.7/data",
                        "dataset":"CFE_test",
                        "expno":"991",
                        "procno":"1",
                        "rowno":"3"}

# window of interest
window=(-0.2, 0.2)

# create Spectrum object
sp = spectrum.Spectrum(data=test_synthetic_dataset, window=window)

# perform peak picking
peak_table = sp.peak_picking(1e6)

# show results
print(peak_table)

# plot peak picking results
fig = sp.plot(pp=peak_table)
fig.show()

# USER DEFINE SIGNALS WITH HELP OF PEAK TABLE

signals = {"singlet_TSP": {"model":"singlet", "par": {"x0": {"ini":0.0, "lb":-0.05, "ub":0.05}}}}

#signals = {"singlet_TSP": {"model":"singlet", "par": {"x0": {"ini":0.0, "lb":-0.05, "ub":0.05}}},
#           "doublet_TSP": {"model":"doublet", "par": {"x0": {"ini":-0.01, "lb":-0.01, "ub":0.01}, "J": {"ini":0.147, "lb":0.14, "ub":0.15}, "lw": {"ini":0.001}}}}

# build model containing all signals
sp.build_model(signals=signals, available_models=available_models)

# model parameters can be updated
sp.update_params({"singlet_TSP": {"par": {"intensity": {"ini":1e6, "ub":1e12}}}})
#sp.update_params({"doublet_TSP": {"par": {"intensity": {"ini":1e8, "lb":5e7, "ub":1e9}}}})
sp.update_offset(offset={})
print(sp.params)

# fit spectrum
sp.fit()

# display estimated parameters
sp.params

# plot sim vs meas
fig = sp.plot(ini=True, fit=True)
fig.show()

