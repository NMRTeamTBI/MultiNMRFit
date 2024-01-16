import streamlit as st
from sess_i.base.main import SessI
import numpy as np

st.set_page_config(page_title="Process ref spectrum",layout="wide")
st.title("Process reference spectrum")

session = SessI(
    session_state = st.session_state,
    page = "Process ref spectrum"
)

if session.object_space["steps_to_show"]["clustering"]:

    # get process
    process = session.object_space["process"]

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
                value = session.widget_space["spectrum_limit_max"]
                )
            
    with col3:
        spec_lim_min = st.number_input(
                label="Spectral limits (min)",
                key="spectrum_limit_min",
                value = session.widget_space["spectrum_limit_min"]
                )

    session.register_widgets({
            "reference_spectrum": reference_spectrum,
            "spectrum_limit_max": spec_lim_max,
            "spectrum_limit_min": spec_lim_min,
        })
    
    # update reference spectrum when widgets' values are changed
    ppm_step = 0.01
    if process.ref_spectrum_rowno != reference_spectrum or np.abs(process.ppm_limits[0]-spec_lim_min) > ppm_step or np.abs(process.ppm_limits[1]-spec_lim_max) > ppm_step:
        process.set_ref_spectrum(session.widget_space["reference_spectrum"], window=(spec_lim_min, spec_lim_max))
        session.object_space["steps_to_show"]["build_model"] = False
        session.object_space["steps_to_show"]["fit_ref"] = False
        session.object_space["steps_to_show"]["fit_all"] = False
        session.object_space["steps_to_show"]["visu"] = False

else:

    st.warning("Please load a dataset to process.")


with st.form("Clustering"):
    if session.object_space["steps_to_show"]["clustering"]:
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

        # Initialize user_models from session state if exists else empty
        #user_models = {}
        #if not session.object_space["user_models"]:
        #    user_models = {}
        #else:
        #    user_models = session.object_space["user_models"]
            # Initialize cluster IDs from previous run on page
            #peak_table["cID"] = [key for key in user_models.keys()]
        #if not session.object_space["user_models"]:
        #    user_models = {}
        #else:
        #    user_models = session.object_space["user_models"]
            # Initialize cluster IDs from previous run on page
            #peak_table["cID"] = [key for key in user_models.keys()]

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
            process.edited_peak_table = edited_peak_table
            process.user_models = {}
            session.object_space["steps_to_show"]["build_model"] = True
            session.object_space["steps_to_show"]["fit_ref"] = False
            session.object_space["steps_to_show"]["fit_all"] = False
            session.object_space["steps_to_show"]["visu"] = False


with st.form("create model"):

    if session.object_space["steps_to_show"]["build_model"]:

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
            session.object_space["steps_to_show"]["fit_ref"] = True
            session.object_space["steps_to_show"]["fit_all"] = False
            session.object_space["steps_to_show"]["visu"] = False

if session.object_space["steps_to_show"]["fit_ref"]:
    with st.form("Fit reference spectrum"):

        st.write("### Parameters")

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
            process.fit_reference_spectrum()

            session.object_space["steps_to_show"]["fit_all"] = True
            session.object_space["steps_to_show"]["visu"] = False

        # show last fit
        if process.ref_spectrum.fit_results is not None:

            # plot fit results
            fig = process.ref_spectrum.plot(ini=True, fit=True)
            fig.update_layout(autosize=False, width=800, height=600)
            fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15)) 
            st.plotly_chart(fig)

if session.object_space["steps_to_show"]["fit_ref"]:
    if process.ref_spectrum.fit_results is not None:
        st.success("Reference spectrum has been fitted.")


