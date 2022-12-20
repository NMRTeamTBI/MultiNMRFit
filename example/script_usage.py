import logging
import multinmrfit.base.spectrum as spectrum
import pandas as pd
import multinmrfit.base.load_models as lm


# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
strm_hdlr = logging.StreamHandler()
strm_hdlr.setFormatter(formatter)
logger.addHandler(strm_hdlr)

# get available models
models = lm.get_models()

# load spectrum
df_data = pd.read_table("C:/Users/millard/Documents/GIT/multinmrfit/code/multinmrfit/example/data/data_sim_nmrfit.csv", sep="\t")

# define signals
signals = {"singlet_1":{"model":"singlet", "par":{"x0":{"ini":7.8, "lb":7.5, "ub":8.0}}},
           "singlet_2":{"model":"singlet", "par":{"x0":{"ini":8.4, "lb":8.3, "ub":8.6}}},
           "singlet_TSP":{"model":"singlet", "par":{"x0":{"ini":0.03, "lb":-0.05, "ub":0.05}}},
           "doublet":{"model":"doublet", "par":{"x0":{"ini":6.0, "lb":5.5, "ub":6.5}, "J1":{"ini":0.09}}},
           "triplet_T":{"model":"triplet", "par":{"x0":{"ini":8.95, "lb":8.7, "ub":9.0}, "J1":{"ini":0.09}}}}

# create spectrum object
sp = spectrum.Spectrum(df_data, signals=signals, models=models, offset=False)

# simulate from initial parameters
res_sim = sp.simulate(sp.params['ini'].values.tolist())

# fit spectrum
sp.fit()

# display parameters
sp.params

# plot sim vs meas
sp.plot()



