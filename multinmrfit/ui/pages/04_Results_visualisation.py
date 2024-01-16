import streamlit as st
import multinmrfit
from sess_i.base.main import SessI


session = SessI(
    session_state = st.session_state,
    page="Results visualization"
)

st.title("Results visualization")


if session.object_space["steps_to_show"]["visu"]:
    
    process = session.get_object(key="process")

    spectra_list = sorted(list(process.results.keys()))

    spectrum = st.selectbox(
                label="Select spectrum",
                key="plot_spectrum",
                options=spectra_list,
                index=0,
                help="Select the spectrum to show"
                )

    fig = process.results[spectrum].plot(ini=True, fit=True)
    fig.update_layout(autosize=False, width=800, height=600)
    fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15)) 
    st.plotly_chart(fig)
    
else:

    st.warning("No results to display, please process some spectra first.")
    