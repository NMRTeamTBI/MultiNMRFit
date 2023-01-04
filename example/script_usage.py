import logging
import multinmrfit.base.spectrum as spectrum
import pandas as pd
import multinmrfit.base.io as io


# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
strm_hdlr = logging.StreamHandler()
strm_hdlr.setFormatter(formatter)
logger.addHandler(strm_hdlr)

# get available models
available_models = io.IoHandler.get_models()

# define data to process
data_path="C:/Bruker/TopSpin4.0.7/data"
experiment="CFE_test"
expno="991"
procno="1"
rowno=3
window=(-0.2, 0.2)

# create spectrum object
sp = spectrum.Spectrum(data_path, experiment, expno, procno, rowno=rowno, window=window)

# perform peak picking
peak_table = sp.peak_picking(float(1e9))

# show results
print(peak_table)

# USER DEFINE SIGNALS WITH HELP OF PEAK TABLE

signals = {"singlet_TSP":{"model":"singlet", "par":{"x0":{"ini":0.0, "lb":-0.05, "ub":0.05}}}}

# build model containing all signals
sp.build_model(signals=signals, available_models=available_models)

# params may be adjusted at any time
sp.set_params({"singlet_TSP":{"par":{"x0":{"ini":0.001, "ub":0.06}}}})
print(sp.params)

# fit spectrum
sp.fit()

# display estimated parameters
sp.params

# plot sim vs meas
fig = sp.plot()
fig.show()

