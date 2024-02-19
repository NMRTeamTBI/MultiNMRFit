import streamlit as st
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

        # start_time = st.slider(
        #             label="Select spectrum",
        #             key="plot_spectrum",
        #             value=datetime(2020, 1, 1, 9, 30),
        #             format="MM/DD/YY - hh:mm")
        
        show_ini = st.checkbox('Show spectrum for initial values', value=session.widget_space["show_ini"], key="show_ini")
        show_ind_signals = st.checkbox('Show individual signals', value=session.widget_space["show_ind_signals"], key="show_ind_signals")

        fig = process.results[spectrum].plot(ini=True, fit=True, colored_area=True)
        fig.update_layout(autosize=False, width=800, height=600)
        fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15))
        if not show_ini:
            fig.for_each_trace(lambda trace: trace.update(visible="legendonly") if trace.name in ["initial values"] else ())
        if not show_ind_signals:
            fig.for_each_trace(lambda trace: trace.update(visible="legendonly") if "signal" in trace.name else ())
        st.plotly_chart(fig)

        session.register_widgets({
            "show_ini": show_ini,
            "show_ind_signals": show_ind_signals
        })

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

        process.consolidate_results()
        # signal_list = list(process.results[1].params.signal_id.unique())
        # signal = st.selectbox(
        #             label="Select signal",
        #             key="signal_to_show",
        #             options = signal_list,
        #             index=0,
        #             help="Select the signal id to show as function of index"
        # )
        # parameter_list = process.results[1].params.par.loc[process.results[1].params.signal_id==signal]
        # # add integral as choice for the menu        
        # parameter_list.loc[len(parameter_list)] = 'integral'

        # parameter = st.selectbox(
        #             label="Select parameter",
        #             key="parameter_to_show",
        #             options=parameter_list,
        #             index=0,
        #             help="Select the parameter to show as function of index"
        # )

        # params_all = process.select_params(signal,parameter,spectra_list)
        
        # fig = process.plot(params=params_all)
        # st.plotly_chart(fig)
        
        # save_txt = st.checkbox('Save text files', value=session.widget_space["save_txt"], key="save_txt")
        # if save_txt:
        #     process.save_results_to_file(spectra_list)
        #     st.info(f"Results text files have been saved")
        
    else:
        st.warning("No results to display, please process some spectra first.")
