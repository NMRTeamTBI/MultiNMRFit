import streamlit as st
from sess_i.base.main import SessI
import multinmrfit.ui.utils as utils
import numpy as np

st.set_page_config(page_title="Clustering",layout="wide")
st.title("Process reference spectrum")

session = SessI(
    session_state = st.session_state,
    page = "clustering"
)

if session.object_space["steps_to_show"]["clustering"]:

    # get process
    process = session.object_space["process"]

    # set default parameters
    session.set_widget_defaults(
        reference_spectrum = process.spectra_list[0],
        spectrum_limit_min = float(process.ppm_limits[0]),
        spectrum_limit_max = float(process.ppm_limits[1])
    )

    # add widgets
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
    
    ppm_step = 0.01
    if process.ref_spectrum_rowno != reference_spectrum or np.abs(process.ppm_limits[0]-spec_lim_min) > ppm_step or np.abs(process.ppm_limits[1]-spec_lim_max) > ppm_step:
        # update reference spectrum
        process.set_ref_spectrum(session.widget_space["reference_spectrum"], window=(spec_lim_min, spec_lim_max))

else:

    st.write("Please load a dataset to process...")


with st.form("Clustering"):
    if session.object_space["steps_to_show"]["clustering"]:
        st.write("### Peak picking & Clustering")
        peakpicking_threshold = st.number_input(
            label="Enter peak picking threshold",
            key = "peakpicking_threshold",
            value = process.peakpicking_threshold,
            step=1e5,
            help="Enter threshold used for peak detection"
            )

        if peakpicking_threshold != process.peakpicking_threshold:
            process.update_pp_threshold(peakpicking_threshold)
        #process.peakpicking_threshold = peakpicking_threshold

        #peak_table = process.ref_spectrum.peak_picking(process.peakpicking_threshold)

        #st.dataframe(
        #    peak_table,
        #    column_config={
        #        'cID':None,
        #    },
        #    hide_index=True
        #    )
        #st.write("Peaks detected")

        fig = process.ref_spectrum.plot(pp=process.edited_peak_table, threshold=process.peakpicking_threshold)
        fig.update_layout(autosize=False, width=900, height=500)
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

        #if process.edited_peak_table is None:

            #edited_peak_table = st.data_editor(
            #    process.edited_peak_table,
            #    column_config={
            #        "ppm":"peak position",
            #        "intensity":"peak intensity",
            #        "cID":"cluster ID"
            #    },
            #    hide_index=True
            #    )
        #else:
        edited_peak_table = st.data_editor(
            process.edited_peak_table,
            column_config={
                    "ppm":"peak position",
                    "intensity":"peak intensity",
                    "cID":"cluster ID"
                },
                hide_index=True
                )

        
        # !!! Needs be clicked twice before it does something correcly otherwise missing the last row !!!#
        create_models = st.form_submit_button("Assign peaks") 

        if create_models:
            process.edited_peak_table = edited_peak_table
            process.user_models = {}

            session.object_space["steps_to_show"]["build_model"] = True
            session.object_space["steps_to_show"]["fit_ref"] = False
            session.object_space["steps_to_show"]["fit_all"] = False


with st.form("create model"):

    if session.object_space["steps_to_show"]["build_model"]:

        clusters_and_models = process.model_cluster_assignment(process.edited_peak_table)

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
                    #index=user_models[key]["model_idx"] if user_models else 0,
                    key=f"Parameter_value_{key}"
                    )

            process.user_models[key] = {'n':clusters_and_models[key]['n'],
                                'model':model,
                                "model_idx": options.index(model)}

        #process.user_models = user_models

        fitting = st.form_submit_button("Build model")
        
        if fitting:
            process.create_signals(process.user_models, process.edited_peak_table)
        

            session.object_space["steps_to_show"]["fit_ref"] = True
            session.object_space["steps_to_show"]["fit_all"] = False
            with st.expander(label="test", expanded=True):
                st.write(process.user_models)
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

