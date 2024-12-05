import streamlit as st
from sess_i.base.main import SessI


session = SessI(
    session_state=st.session_state,
    page="Results visualization"
)

st.title("Results visualization")

process = session.get_object(key="process")


def update_checkbox(widget):
    session.register_widgets({widget: not session.widget_space[widget]})


if process is None:

    st.warning("No results to display, please process some spectra first.")

else:
    
    # consolidate the results only if not done yet
    if session.get_object(key="consolidate"):
        with st.spinner('Results consolidation in progress...'):
            process.consolidate_results()
            session.object_space["consolidate"] = False

    if len(process.results):
        with st.container(border=True):

            st.write("### Processed spectra")

            spectra_list = sorted(list(process.results.keys()))

            if len(spectra_list) > 1:
                spectrum = st.select_slider("Select spectrum", options=spectra_list, key="plot_spectrum")
            else:
                spectrum = spectra_list[0]
                st.write(f"Only one spectrum has been processed: {spectrum}")
            session.register_widgets({"plot_spectrum": spectrum})

            regions = sorted(list(process.results[spectrum].keys()))
            idx = regions.index(session.widget_space["region_plot"]) if session.widget_space["region_plot"] in regions else 0

            col1, col2 = st.columns(2)
            with col1:
                region = st.selectbox(
                    label="Select region",
                    key="region_plot",
                    options=regions,
                    index=idx
                )
                session.register_widgets({
                    "region_plot": region
                })

            col1, col2 = st.columns(2)

            with col1:
                show_ini = st.checkbox('Show spectrum for initial values',
                                       value=session.widget_space["show_ini"], key="show_ini", on_change=update_checkbox, args=["show_ini"])
            with col2:
                show_ind_signals = st.checkbox(
                    'Show individual signals', value=session.widget_space["show_ind_signals"], key="show_ind_signals", on_change=update_checkbox, args=["show_ind_signals"])

            fig = process.results[spectrum][region].plot(ini=True, fit=True, colored_area=True)
            fig.update_layout(autosize=False, width=800, height=600)
            fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15))
            if not show_ini:
                fig.for_each_trace(lambda trace: trace.update(visible="legendonly") if trace.name in ["initial values"] else ())
            if not show_ind_signals:
                fig.for_each_trace(lambda trace: trace.update(visible="legendonly") if "signal" in trace.name else ())
            st.plotly_chart(fig, theme=None)

            st.markdown("**Parameters**")

            tmp = process.results[spectrum][region].params.style.apply(process.highlighter, axis=None)

            st.data_editor(
                tmp,
                hide_index=True,
                disabled=["signal_id", "model", "par", "opt", "opt_sd", "integral", "ini", "ub", "lb"]
            )

        with st.container(border=True):
            st.write("### Fitting results")

            # signal selection to visualize
            col1, col2 = st.columns(2)

            with col1:

                signal_list = process.compounds()
                signal = st.selectbox(
                    label="Select signal",
                    key="signal_to_show",
                    options=signal_list,
                    index=0,
                    help="Select the signal id to show as function of index"
                )

            # parameter selection to visualize
            with col2:

                parameter_list = list(process.consolidated_results[process.consolidated_results.signal_id == signal].par.unique())

                parameter = st.selectbox(
                    label="Select parameter",
                    key="parameter_to_show",
                    options=parameter_list,
                    index=parameter_list.index("integral"),
                    help="Select the parameter to show as function of index"
                )

            y_zero = st.checkbox('Set y axis to zero', value=True, key="zero")
            fig = process.plot(signal, parameter)
            fig.update_layout(xaxis_title="spectrum")
            if y_zero:
                fig.update_yaxes(rangemode="tozero")
            st.plotly_chart(fig, theme=None)

        with st.container(border=True):
            st.write("### Export")

            col1, col2 = st.columns(2)

            with col1:
                export_sel = st.selectbox(
                    label="Export results to tsv",
                    key="export",
                        options=["all parameters/signals", "specific parameters/signals", "spectra data"],
                    index=0
                )
                save_button = st.button('Export')
            with col2:
                if export_sel == "all parameters/signals":
                    filename = st.text_input(
                        label="Enter filename",
                        value=process.filename
                    )

                elif export_sel == "specific parameters/signals":
                    signal = st.selectbox(
                        label="Signal",
                        options=signal_list,
                        index=0
                    )

                    # parameter selection to save
                    parameter_list = process.consolidated_results[process.consolidated_results.signal_id == signal].par.unique()

                    parameter = st.selectbox(
                        label="Parameter",
                        key="parameter_to_save",
                        options=parameter_list,
                        index=0,
                        help="Select the parameter to save"
                    )

                    filename = st.text_input(
                        label="Filename",
                    )

                elif export_sel == "spectra data":
                    spectrum = st.selectbox(
                        label="Select spectrum",
                        key="spectrum_to_save",
                        options=spectra_list,
                    )
                    regions = sorted(list(process.results[spectrum].keys()))
                    idx = regions.index(session.widget_space["region_plot"]) if session.widget_space["region_plot"] in regions else 0

                    region = st.selectbox(
                        label="Select region",
                        key="spectrum_region_to_save",
                        options=regions,
                        index=idx
                    )

                    session.register_widgets({
                        "spectrum_region_to_save": region
                    })

                    filename = st.text_input(
                        label="Filename",
                    )
                else:
                    st.warning("Selection error")

            if save_button:
                if export_sel == "all parameters/signals":
                    process.save_consolidated_results()
                    st.info(f"Results files exported")
                elif export_sel == "specific parameters/signals":
                    process.save_consolidated_results(data=process.select_params(signal, parameter), partial_filename=filename)
                    st.info(f"Results files exported")
                elif export_sel == "spectra data":
                    process.save_spetrum_data(spectrum, region, filename)
                    st.info(f"Spectrum file exported")

    else:
        st.warning("No results to display, please process some spectra first.")
