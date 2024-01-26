import streamlit as st
import multinmrfit
import pandas as pd
import numpy as np
from sess_i.base.main import SessI


session = SessI(
    session_state = st.session_state,
    page="Results visualization"
)

st.title("Results visualization")

process = session.get_object(key="process")



if process is None:

    st.warning("No results to display, please process some spectra first.")

else:

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

       #parameters = st.data_editor(
       #         process.results[spectrum].params,
       #             hide_index=True,
       #             disabled=["signal_id", "model", "par", "opt", "opt_sd", "integral", "ini", "ub", "lb"]
       #             )
        
        tmp = process.results[spectrum].params.style.apply(process.highlighter, axis=None)

        st.data_editor(
                    tmp,
                    hide_index=True,
                    disabled=["signal_id", "model", "par", "opt", "opt_sd", "integral", "ini", "ub", "lb"]
                    )

        signal_list = list(process.results[1].params.signal_id.unique())
        signal = st.selectbox(
                    label="Select signal",
                    key="signal_to_show",
                    options = signal_list,
                    index=0,
                    help="Select the signal id to show as function of index"
        )
        parameter_list = process.results[1].params.par.loc[process.results[1].params.signal_id==signal]
        parameter = st.selectbox(
                    label="Select parameter",
                    key="parameter_to_show",
                    options=parameter_list,
                    index=0,
                    help="Select the parameter to show as function of index"
        )

        # st.write(
        #     process.results[1].params.loc[
        #         (process.results[1].params.par==parameter) &
        #         (process.results[1].params.signal_id==signal)].opt #.par.loc[process.results[1].params.signal_id==signal]
        #     )
        params_all = process.select_params(signal,parameter,spectra_list)
        
        fig = process.plot(params=params_all)
        st.plotly_chart(fig)

        st.write(params_all)
    else:
        st.warning("No results to display, please process some spectra first.")
