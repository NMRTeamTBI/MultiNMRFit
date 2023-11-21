import streamlit as st
import logging
import sys
import pandas as pd


from sess_i.base.main import SessI
import multinmrfit.base.spectrum as spectrum
import multinmrfit.base.io as io

st.set_page_config(page_title="Clustering")
st.title("Clustering")

session_clustering  = SessI(st.session_state, "clustering")
session_io          = SessI(st.session_state, "inputs_outputs")

session_clustering.set_widget_defaults(
    reference_spectrum      =   1,
    peakpicking_threshold   =   1e5,
    spectrum_limit_max      =   10,
    spectrum_limit_min      =   8,
)

test_synthetic_dataset = pd.read_table("./example/data/data_sim_nmrfit.csv", sep="\t")

# with st.form('Reference spectrum'):
st.write("Reference spectrum")

reference_spectrum = st.number_input(
        label="Enter the number of the reference spectrum",
        key = "reference_spectrum",
        value = session_clustering.widget_space["reference_spectrum"],
        help="Enter the number of the spectrum used for peak picking and clustering"
        )

# peakpicking_threshold = st.number_input(
#         label="Enter peak picking threshold",
#         key = "peakpicking_threshold",
#         value = session_clustering.widget_space["peakpicking_threshold"],
#         help="Enter threshold used for peak detection"
#         )

col1, col2 = st.columns(2)
with col1:
    spec_lim_max = st.number_input(
        label="Spectral limits (max)",
        key="spectrum_limit_max",
        value = session_clustering.widget_space["spectrum_limit_max"]
        )
    
with col2:
    spec_lim_min = st.number_input(
        label="Spectral limits (min)",
        key="spectrum_limit_min",
        value = session_clustering.widget_space["spectrum_limit_min"]
        )


session_clustering.register_widgets({
    "reference_spectrum"    : reference_spectrum,
    "spectrum_limit_max"    : spec_lim_max,
    "spectrum_limit_min"    : spec_lim_min,
})

sp = spectrum.Spectrum(data=test_synthetic_dataset,window=(session_clustering.widget_space["spectrum_limit_min"],session_clustering.widget_space["spectrum_limit_max"]))
fig = sp.plot(exp=True)
fig.update_layout(autosize=False, width=670, height=400)
st.plotly_chart(fig)  



peak_table = sp.peak_picking(session_clustering.widget_space["peakpicking_threshold"])
fig = sp.plot(pp=peak_table)
st.write(peak_table)
st.plotly_chart(fig)