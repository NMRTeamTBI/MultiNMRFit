import streamlit as st
from sess_i.base.main import SessI


session = SessI(
    session_state = st.session_state,
    page="Results visualization"
)

st.title("Results visualization")

process = session.get_object(key="process")

def update_checkbox(widget):
    session.register_widgets({widget: not session.widget_space[widget]})
    
    
if process is None:

    st.warning("No results to display, please process some spectra first.")

else:

    if len(process.results):
        with st.container(border=True):
            
            st.write("### Spectra")

            spectra_list = sorted(list(process.results.keys()))

            col1, col2 = st.columns(2)

            with col1:
                spectrum = st.selectbox(
                            label="Select spectrum",
                            key="plot_spectrum",
                            options=spectra_list,
                            )
            
            regions = sorted(list(process.results[spectrum].keys()))
            idx = regions.index(session.widget_space["region_plot"]) if session.widget_space["region_plot"] in regions else 0

            with col2:
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
                show_ini = st.checkbox('Show spectrum for initial values', value=session.widget_space["show_ini"], key="show_ini", on_change=update_checkbox, args=["show_ini"])
            with col2:
                show_ind_signals = st.checkbox('Show individual signals', value=session.widget_space["show_ind_signals"], key="show_ind_signals", on_change=update_checkbox, args=["show_ind_signals"])
            
            fig = process.results[spectrum][region].plot(ini=True, fit=True, colored_area=True)
            fig.update_layout(autosize=False, width=800, height=600)
            fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15))
            if not show_ini:
                fig.for_each_trace(lambda trace: trace.update(visible="legendonly") if trace.name in ["initial values"] else ())
            if not show_ind_signals:
                fig.for_each_trace(lambda trace: trace.update(visible="legendonly") if "signal" in trace.name else ())
            st.plotly_chart(fig)

            st.write("### Parameters")

            tmp = process.results[spectrum][region].params.style.apply(process.highlighter, axis=None)

            st.data_editor(
                        tmp,
                        hide_index=True,
                        disabled=["signal_id", "model", "par", "opt", "opt_sd", "integral", "ini", "ub", "lb"]
                        )

            # consolidate the results 
            process.consolidate_results()

        with st.container(border=True):
            st.write("### Plot")

            # signal selection to visualize
            col1, col2 = st.columns(2)

            with col1:
            
                signal_list = process.compounds()      
                signal = st.selectbox(
                            label="Select signal",
                            key="signal_to_show",
                            options = signal_list,
                            index=0,
                            help="Select the signal id to show as function of index"
                )

            # parameter selection to visualize
            with col2:

                parameter_list = list(process.consolidated_results[process.consolidated_results.signal_id==signal].par.unique())

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
            st.plotly_chart(fig)

        with st.container(border=True):
            st.write("### Export")

            col1, col2 = st.columns(2)

            with col1:
                export_sel = st.selectbox(
                        label="Export data to tsv",
                        key="export",
                        options=["all data", "specific data","spectrum data"],
                        index=0
                        )
                save_button = st.button('Export')
            with col2:
                if export_sel == "all data":
                    filename = st.text_input(
                            label="Enter filename",
                            value=process.filename
                            )

                elif export_sel == "specific data":
                    signal = st.selectbox(
                                label="Signal",
                                options = signal_list,
                                index=0
                                )

                    # parameter selection to save
                    parameter_list = process.consolidated_results[process.consolidated_results.signal_id==signal].par.unique()

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
                    
                elif export_sel == "spectrum data":
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
                if export_sel == "all data":
                    process.save_consolidated_results()
                    st.info(f"Results files exported")
                elif export_sel == "specific data":
                    process.save_consolidated_results(data=process.select_params(signal,parameter),partial_filename=filename)
                    st.info(f"Results files exported")
                elif export_sel == "spectrum data":
                    process.save_spetrum_data(spectrum,region,filename)
                    st.info(f"Spectrum file exported")

                    # print(process.results[spectrum][region].ppm,process.results[spectrum][region].intensity,process.results[spectrum][region].fit_results.best_fit)
    else:
        st.warning("No results to display, please process some spectra first.")
