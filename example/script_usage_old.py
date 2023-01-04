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

# load spectrum
#df_data = pd.read_table("C:/Users/millard/Documents/GIT/multinmrfit/code/multinmrfit/example/data/data_sim_nmrfit.csv", sep="\t")
df_data = pd.read_table("./data/data_sim_nmrfit.csv", sep="\t")


# ############
# ## FULL SPECTRUM (takes time and not stable)
# ############

# # define signals
# signals = {"singlet_1":{"model":"singlet", "par":{"x0":{"ini":7.8, "lb":7.5, "ub":8.0}}},
#            "singlet_2":{"model":"singlet", "par":{"x0":{"ini":8.4, "lb":8.3, "ub":8.6}}},
#            "singlet_TSP":{"model":"singlet", "par":{"x0":{"ini":0.03, "lb":-0.05, "ub":0.05}}},
#            "doublet":{"model":"doublet", "par":{"x0":{"ini":6.0, "lb":5.5, "ub":6.5}, "J1":{"ini":0.09}}},
#            "triplet_T":{"model":"triplet", "par":{"x0":{"ini":8.95, "lb":8.7, "ub":9.0}, "J1":{"ini":0.09}}}}

# # create spectrum object
# sp = spectrum.Spectrum(df_data, signals=signals, models=models)

# # simulate from initial parameters
# res_sim = sp.simulate(sp.params['ini'].values.tolist())

# # fit spectrum
# #sp.fit(method="differential_evolution")
# sp.fit()

# # display parameters
# sp.params

# # plot sim vs meas
# sp.plot()


############
## PARTIAL SPECTRUM 1
############

# define signals
#signals = {"singlet_1":{"model":"singlet", "par":{"x0":{"ini":7.8, "lb":7.5, "ub":8.0}}},
#           "singlet_2":{"model":"singlet", "par":{"x0":{"ini":8.4, "lb":8.3, "ub":8.6}}},
#           "triplet_T":{"model":"triplet", "par":{"x0":{"ini":8.95, "lb":8.7, "ub":9.0}, "J1":{"ini":0.09}}}}


# create spectrum object


data_path="C:/Bruker/TopSpin4.0.7/data"
experiment="CFE_test"
expno="991"
procno="1"
rowno=3
window=(-0.2, 0.2)


sp = spectrum.Spectrum(data_path, experiment, expno, procno, rowno=rowno, window=window)

peak_table = sp.peak_picking(float(1e9))

print(peak_table)

# USER DEFINE SIGNALS WITH HELP OF PEAK TABLE

signals = {"singlet_TSP":{"model":"singlet", "par":{"x0":{"ini":0.0, "lb":-0.05, "ub":0.05}}}}

sp.build_model(signals=signals, available_models=available_models)

sp.set_params({"singlet_TSP":{"par":{"x0":{"ini":0.001, "ub":0.06}}}})
print(sp.params)

# fit spectrum
sp.fit()

# display parameters
sp.params

# plot sim vs meas
fig = sp.plot()
fig.show()


exit()

############
## PARTIAL SPECTRUM 2
############

# define signals
signals = {"singlet_TSP":{"model":"singlet", "par":{"x0":{"ini":0.03, "lb":-0.05, "ub":0.05}}}}

# limit spectrum
ppm_max = 0.5
ppm_min = -0.5
df_data_cut = df_data.loc[(df_data['ppm'] < ppm_max) & (df_data['ppm'] > ppm_min)]

# create spectrum object
sp = spectrum.Spectrum(df_data_cut, signals=signals, available_models=available_models, offset={'ini':1.0})

# fit spectrum
#sp.fit(method="differential_evolution")
sp.fit()

# display parameters
sp.params

# plot sim vs meas
fig = sp.plot()
fig.show()



