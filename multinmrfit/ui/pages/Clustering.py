import streamlit as st
import logging
import sys
import pandas as pd


from sess_i.base.main import SessI
import multinmrfit.base.spectrum as spectrum
import multinmrfit.ui.utils as utils

st.set_page_config(page_title="Clustering",layout="wide")
st.title("Clustering")

session = SessI(
    session_state = st.session_state,
    page="clustering"
)

######
# reads-in data 
utils = utils.IoHandler()
dataset = {"data_path":str(st.session_state["Global_Widget_Space"]["inputs_outputs"]['input_exp_data_path']),
           "dataset":str(st.session_state["Global_Widget_Space"]["inputs_outputs"]['input_exp_data_folder']),
           "expno":str(st.session_state["Global_Widget_Space"]["inputs_outputs"]['input_expno']),
           "procno":str(st.session_state["Global_Widget_Space"]["inputs_outputs"]['input_procno']),
           }
# Get n_row from the full experiment
n_row, exp_dim = utils.get_dim(dataset)
# Estimate the ppm limits for the default values
ppm_min, ppm_max = utils.get_ppm_Limits(dataset)
######

session.set_widget_defaults(
    reference_spectrum = 1,
    spectrum_limit_max = ppm_max,
    spectrum_limit_min = ppm_min,
)


with st.expander("Reference spectrum", expanded=True):
    reference_spectrum = st.selectbox(
            label="Select the number of the reference spectrum",
            key = "reference_spectrum",
            options =list(range(1,n_row+1)), 
            help="Select the number of the spectrum used for peak picking and clustering"
            )
    
    col1, col2 = st.columns(2)
    with col1:
        spec_lim_max = st.number_input(
            label="Spectral limits (max)",
            key="spectrum_limit_max",
            value = session.widget_space["spectrum_limit_max"]
            )
        
    with col2:
        spec_lim_min = st.number_input(
            label="Spectral limits (min)",
            key="spectrum_limit_min",
            value = session.widget_space["spectrum_limit_min"]
            )


    session.register_widgets({
        "reference_spectrum"    : reference_spectrum, #account for python vs data shape
        "spectrum_limit_max"    : spec_lim_max,
        "spectrum_limit_min"    : spec_lim_min,
    })

    dataset['rowno'] = session.widget_space["reference_spectrum"]-1

    sp = spectrum.Spectrum(
        data=dataset,
        window=(
            min(session.widget_space["spectrum_limit_min"],session.widget_space["spectrum_limit_max"]),
            max(session.widget_space["spectrum_limit_min"],session.widget_space["spectrum_limit_max"]))
            )
    
    fig = sp.plot(exp=True)
    fig.update_layout(autosize=False, width=900, height=500)
    st.plotly_chart(fig)  

    session.register_object(
        obj=sp,
        key="reference_spectrum"
    )

with st.form("Clustering"):
    st.write("Peak picking & CLustering")
    peakpicking_threshold = st.number_input(
        label="Enter peak picking threshold",
        key = "peakpicking_threshold",
        value = max(session.object_space["reference_spectrum"].intensity)/5,
        step=1e5,
        help="Enter threshold used for peak detection"
        )

    session.register_widgets({
        "peakpicking_threshold"    : peakpicking_threshold,
    })

    st.write("List of detected peaks")
    peak_table = sp.peak_picking(session.widget_space["peakpicking_threshold"])
    edited_peak_table = st.data_editor(peak_table)

    session.register_widgets({
        "edited_peak_table"    : edited_peak_table,
    })
    st.write(session)
    st.write("Plot with detected peaks")

    fig = sp.plot(pp=peak_table,threshold=session.widget_space["peakpicking_threshold"])
    fig.update_layout(autosize=False, width=900, height=500)
    st.plotly_chart(fig)

    fitting = st.form_submit_button("Fitting")

if fitting:
    with st.expander("Fitting the reference spectrum", expanded=True): 
        available_models = io.IoHandler.get_models()
        signals = {"singlet_TSP": {"model":"singlet", "par": {"x0": {"ini":0.0, "lb":-0.05, "ub":0.05}}}}
        sp.build_model(signals=signals, available_models=available_models)

        sp.fit()
        fig = sp.plot(ini=True, fit=True)
        fig.update_layout(autosize=False, width=900, height=900)
        st.plotly_chart(fig)

