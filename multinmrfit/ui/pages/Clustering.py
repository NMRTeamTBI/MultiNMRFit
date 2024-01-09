import streamlit as st
import logging
import sys
import pandas as pd

from sess_i.base.main import SessI
import multinmrfit.base.spectrum as spectrum
import multinmrfit.ui.utils as utils

st.set_page_config(page_title="Clustering",layout="wide")
st.title("Process reference spectrum")

session = SessI(
    session_state = st.session_state,
    page = "clustering"
)

# load processing state
steps_done = session.object_space["steps_done"]

# get dataset
dataset = {"data_path": str(st.session_state["Global_Widget_Space"]["inputs_outputs"]['input_exp_data_path']),
           "dataset": str(st.session_state["Global_Widget_Space"]["inputs_outputs"]['input_exp_data_folder']),
           "expno": str(st.session_state["Global_Widget_Space"]["inputs_outputs"]['input_expno']),
           "procno": str(st.session_state["Global_Widget_Space"]["inputs_outputs"]['input_procno'])
           }

if session.object_space["steps_done"]["load"]:

    # initialize process
    process = utils.Process(dataset, window=None)

    # set default parameters
    session.set_widget_defaults(
        reference_spectrum = process.spectra_list[0],
        spectrum_limit_max = float(process.ppm_limits[0]),
        spectrum_limit_min = float(process.ppm_limits[1])
    )

    with st.form("Reference spectrum"):

        st.write("Define reference spectrum")

        reference_spectrum = st.selectbox(
                label="Select reference spectrum",
                key="reference_spectrum",
                options=process.spectra_list, 
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
            "reference_spectrum": reference_spectrum,
            "spectrum_limit_max": spec_lim_max,
            "spectrum_limit_min": spec_lim_min,
        })

        dataset['rowno'] = session.widget_space["reference_spectrum"]-1

        # build new process
        process = utils.Process(dataset, window=(float(spec_lim_min), float(spec_lim_max)))

        # display reference spectrum
        fig = process.ref_spectrum.plot(exp=True)
        fig.update_layout(autosize=False, width=900, height=500)
        st.plotly_chart(fig)  

        # save process in object space
        session.register_object(obj=process, key="process")

        # validate and go to next step
        create_clusters = st.form_submit_button("Annotate")

        if create_clusters:
            session.object_space["steps_done"]["clustering"] = True
            session.object_space["steps_done"]["fit_ref"] = False
            session.object_space["steps_done"]["fit_all"] = False

else:
    st.write("Please load a dataset to process...")

with st.form("Clustering"):
    if session.object_space["steps_done"]["clustering"]:
        st.write("Peak picking & Clustering")
        peakpicking_threshold = st.number_input(
            label="Enter peak picking threshold",
            key = "peakpicking_threshold",
            value = max(session.object_space["process"].ref_spectrum.intensity)/5,
            step=1e5,
            help="Enter threshold used for peak detection"
            )

        session.register_widgets({
            "peakpicking_threshold": peakpicking_threshold,
        })

        peak_table = process.ref_spectrum.peak_picking(session.widget_space["peakpicking_threshold"])

        #st.dataframe(
        #    peak_table,
        #    column_config={
        #        'cID':None,
        #    },
        #    hide_index=True
        #    )
        #st.write("Peaks detected")

        fig = process.ref_spectrum.plot(pp=peak_table, threshold=session.widget_space["peakpicking_threshold"])
        fig.update_layout(autosize=False, width=900, height=500)
        st.plotly_chart(fig)

        # Initialize user_models from session state if exists else empty
        if not session.object_space["user_models"]:
            user_models = {}
        else:
            user_models = session.object_space["user_models"]
            # Initialize cluster IDs from previous run on page
            peak_table["cID"] = [key for key in user_models.keys()]


        st.write("Peak list")

        edited_peak_table = st.data_editor(
            peak_table,
            column_config={
                "ppm":"peak position",
                "intensity":"peak intensity",
                "cID":"cluster ID"
            },
            hide_index=True
            )
        
        session.register_object(
            obj=edited_peak_table,
            key="edited_peak_table"
        )

        # !!! Needs be clicked twice before it does something correcly otherwise missing the last row !!!#
        create_models = st.form_submit_button("Build model") 

        if create_models:
            session.object_space["steps_done"]["fit_ref"] = True
            session.object_space["steps_done"]["fit_all"] = False


with st.form("create and update models"):

    if session.object_space["steps_done"]["fit_ref"]:

        clusters_and_models = process.model_cluster_assignment(edited_peak_table)

        col1, col2 = st.columns(2)

        with col1:
            st.write("Cluster ID")
        with col2:
            st.write("Models")

        for key in clusters_and_models:

            options = [i for i in clusters_and_models[key]['models']]
            # st.write(clusters_and_models)

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
                    index=user_models[key]["model_idx"] if user_models else 0,
                    # value=user_models[key]["model"] if user_models else None,
                    key=f"Parameter_value_{key}"
                    )

            user_models[key] = {'n':clusters_and_models[key]['n'],
                                'model':model,
                                "model_idx": options.index(model)}

        session.register_object(obj=user_models, key="user_models")

        fitting = st.form_submit_button("Fit reference spectrum")
        
        if fitting:
            session.object_space["steps_done"]["fit_all"] = True
            with st.expander(label="test", expanded=True):
                example = session.get_object(
                    key = "user_models"
                    )   
                st.write(example)
#     with st.expander("test", expanded=True):
#         st.write(session.widget_space['user_models'])
#         st.write('##')
#     with st.expander("Fitting the reference spectrum", expanded=True): 
#         st.write(edited_peak_table)
#         available_models = io.IoHandler.get_models()
#         signals = {"singlet_TSP": {"model":"singlet", "par": {"x0": {"ini":0.0, "lb":-0.05, "ub":0.05}}}}
#         sp.build_model(signals=signals, available_models=available_models)

#         sp.fit()
#         fig = sp.plot(ini=True, fit=True)
#         fig.update_layout(autosize=False, width=900, height=900)
#         st.plotly_chart(fig)

