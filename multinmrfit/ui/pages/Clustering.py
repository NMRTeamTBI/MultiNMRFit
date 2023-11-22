import streamlit as st
import logging
import sys
import pandas as pd


from sess_i.base.main import SessI
import multinmrfit.base.spectrum as spectrum
import multinmrfit.base.io as io

st.set_page_config(page_title="Clustering",layout="wide")
st.title("Clustering")

session = SessI(
    session_state = st.session_state,
    page="clustering"
)

session.set_widget_defaults(
    reference_spectrum = 1,
    spectrum_limit_max = 10.0,
    spectrum_limit_min = 8.0,
)

test_synthetic_dataset = pd.read_table("./example/data/data_sim_nmrfit.csv", sep="\t")

with st.expander("Reference spectrum", expanded=True):
    st.write("Reference spectrum")

    reference_spectrum = st.number_input(
            label="Enter the number of the reference spectrum",
            key = "reference_spectrum",
            value = session.widget_space["reference_spectrum"],
            help="Enter the number of the spectrum used for peak picking and clustering"
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
        "reference_spectrum"    : reference_spectrum,
        "spectrum_limit_max"    : spec_lim_max,
        "spectrum_limit_min"    : spec_lim_min,
    })

    st.write(session)

    sp = spectrum.Spectrum(
        data=test_synthetic_dataset,
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



with st.expander("Clustering", expanded=True):

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
    edited_df = st.data_editor(peak_table)

    st.write("Plot with detected peaks")

    fig = sp.plot(pp=peak_table)
    fig.update_layout(autosize=False, width=670, height=400)
    st.plotly_chart(fig)
    
    
    sp.fit()
    

