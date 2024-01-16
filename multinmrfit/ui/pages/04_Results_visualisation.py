import streamlit as st
import multinmrfit
from sess_i.base.main import SessI


session = SessI(
    session_state = st.session_state,
    page="Results visualization"
)

st.title("Results visualization")

process = session.get_object(key="process")

if process is not None:
    if len(process.results):

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

        parameters = st.data_editor(
                process.results[spectrum].params,
                    hide_index=True,
                    disabled=["signal_id", "model", "par", "opt", "opt_sd", "integral", "ini", "ub", "lb"]
                    )

    else:
        st.warning("No results to display, please process some spectra first.")

else:
    st.warning("No results to display, please process some spectra first.")
    