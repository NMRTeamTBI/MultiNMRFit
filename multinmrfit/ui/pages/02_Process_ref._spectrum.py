import streamlit as st
from sess_i.base.main import SessI
import numpy as np
import pandas as pd

st.set_page_config(page_title="Process ref spectrum",layout="wide")
st.title("Process reference spectrum")

session = SessI(
    session_state = st.session_state,
    page = "Process ref. spectrum"
)

# get process
process = session.object_space["process"]

if process is None:

    st.warning("Please load a dataset or import a process file.")

else:

    # set default parameters
    session.set_widget_defaults(
        reference_spectrum = process.ref_spectrum_rowno,
        spectrum_limit_min = float(process.ppm_limits[0]),
        spectrum_limit_max = float(process.ppm_limits[1])
    )

    # add widgets
    col1, col2, col3 = st.columns(3)

    with col1:
        reference_spectrum = st.selectbox(
                label="Select reference spectrum",
                key="reference_spectrum",
                options=process.spectra_list,
                index=process.spectra_list.index(process.ref_spectrum_rowno),
                help="Select the spectrum used as reference for peak detection and clustering"
                )

    with col2:
        spec_lim_max = st.number_input(
                label="Spectral limits (max)",
                key="spectrum_limit_max",
                value = session.widget_space["spectrum_limit_max"],
                min_value = min(process.ppm_full) + 0.1,
                max_value = max(process.ppm_full)
                )
            
    with col3:
        spec_lim_min = st.number_input(
                label="Spectral limits (min)",
                key="spectrum_limit_min",
                value = session.widget_space["spectrum_limit_min"],
                min_value = min(process.ppm_full),
                max_value = max(process.ppm_full) - 0.1
                )

    session.register_widgets({
            "reference_spectrum": reference_spectrum,
            "spectrum_limit_max": spec_lim_max,
            "spectrum_limit_min": spec_lim_min,
        })
    
    # update reference spectrum when widgets' values are changed
    ppm_step = 0.01
    if process.ref_spectrum_rowno != reference_spectrum or np.abs(process.ppm_limits[0]-spec_lim_min) > ppm_step or np.abs(process.ppm_limits[1]-spec_lim_max) > ppm_step:
        if (spec_lim_max-spec_lim_min) < 0.1:
            st.error("Error: ppm max must be higher than ppm min.")
        else:                
            process.set_ref_spectrum(session.widget_space["reference_spectrum"], window=(spec_lim_min, spec_lim_max))


    with st.form("Clustering"):

        if process is not None:

            st.write("### Peak picking & Clustering")
            
            peakpicking_threshold = st.number_input(
                label="Peak picking threshold",
                key="peakpicking_threshold",
                value=process.peakpicking_threshold,
                step=1e5,
                help="Enter threshold used for peak detection"
                )

            if peakpicking_threshold != process.peakpicking_threshold:
                process.update_pp_threshold(peakpicking_threshold)

            fig = process.ref_spectrum.plot(pp=process.edited_peak_table, threshold=process.peakpicking_threshold)
            fig.update_layout(autosize=False, width=800, height=500)
            fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15)) 
            st.plotly_chart(fig)

            st.write("Peak list")

            edited_peak_table = st.data_editor(
                process.edited_peak_table,
                column_config={
                        "ppm":"peak position",
                        "intensity":"peak intensity",
                        "cID":"cluster ID",
                        "X_LW":None
                    },
                    hide_index=True,
                    disabled=["ppm", "intensity"]
                    )

            create_models = st.form_submit_button("Assign peaks") 

            if create_models:
                
                clusters = set(list(filter(None, edited_peak_table.cID.values.tolist())))

                if len(clusters):
                    process.edited_peak_table = edited_peak_table
                    process.user_models = {}
                else:
                    st.error("Error: no cluster defined.")


    with st.form("create model"):

        if isinstance(process.edited_peak_table, pd.DataFrame):

            if len(set(list(filter(None, process.edited_peak_table.cID.values.tolist())))):

                st.write("### Model construction")

                clusters_and_models = process.model_cluster_assignment()

                col1, col2 = st.columns(2)

                with col1:
                    st.write("Cluster ID")
                with col2:
                    st.write("Models")

                for key in clusters_and_models:

                    options = [i for i in clusters_and_models[key]['models']]

                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input(
                            label='label',
                            label_visibility='collapsed',
                            value=f"{key} ({clusters_and_models[key]['n']} peaks)",
                            disabled=True
                            )

                    with col2:
                        model = st.selectbox(
                            label='label',
                            label_visibility='collapsed',
                            options=options,
                            index=0,
                            key=f"Parameter_value_{key}"
                            )

                    process.user_models[key] = {'n':clusters_and_models[key]['n'],
                                        'model':model,
                                        "model_idx": options.index(model)}
                
                offset_def = False if not len(process.ref_spectrum.params) else (process.ref_spectrum.offset not in [False, None])
                offset = st.checkbox('offset', value=offset_def)

                fitting = st.form_submit_button("Build model")
                
                if fitting:
                    offs = {} if offset else None
                    process.create_signals(process.user_models, offset=offs)


    if isinstance(process.ref_spectrum.params, pd.DataFrame):

        if len(process.ref_spectrum.params):

            with st.form("Fit reference spectrum"):

                st.write("### Fitting")

                st.write("Parameters")

                parameters = st.data_editor(
                    process.ref_spectrum.params,
                        hide_index=True,
                        disabled=["signal_id", "model", "par", "opt", "opt_sd", "integral"]
                        )
                
                fit_ok = st.form_submit_button("Fit reference spectrum") 

                if fit_ok:

                    # update parameters
                    process.update_params(parameters)

                    # fit reference spectrum
                    with st.spinner('Fitting in progress, please wait...'):
                        process.fit_reference_spectrum()

                # show last fit
                if process.ref_spectrum.fit_results is not None:

                    # plot fit results
                    fig = process.ref_spectrum.plot(ini=True, fit=True)
                    fig.update_layout(autosize=False, width=800, height=600)
                    fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15)) 
                    st.plotly_chart(fig)

                    # save as pickle file
                    process.save_process_to_file()
                    
                    st.success("Reference spectrum has been fitted.")


