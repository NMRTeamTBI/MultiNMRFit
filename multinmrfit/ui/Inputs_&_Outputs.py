""""
First page of the streamlit GUI for NmrFit. Contains logic for handling inputs, analysis, outputs and extra options.
"""

import streamlit as st
import multinmrfit

from utils import directory_selector, map_all_options_to_session_state

# Configure page info
st.set_page_config(page_title=f"NMRFit (v{multinmrfit.__version__})")
st.title(f"Welcome to NMRFit (v{multinmrfit.__version__})")

# Initialize other pages
st.session_state.pages = {f"Page_{num}": False for num in range(1, 5)}
st.session_state.pages["Page 1"] = True

st.header("Use this section to handle inputs and outputs")

# Initialize config file uploader
config_file = st.file_uploader(
    label="Upload configuration file",
    key="page_1_config_file_uploader",
    help="Choose a configuration file to initialize the software with run parameters"
)

# Generate button to select the NMR data folder (Keys should be standardized)
data_folder_path = directory_selector(
    message="Select NMR data directory",
    button_key="page_1_data_path_selector",
    path_key="input_directory"
)

# Generate form that will contain most of the page
input_form = st.form(key="page1_input_form")
# directory_selector("Select input data directory", "main_form_input_button", "input_directory")
with input_form:
    with st.container():
        st.write("Handle Inputs")
        # TODO: Ask if sub-groups should be in containers

        # Add button to enter specific NMR experiment data folder name
        exp_data_folder = st.text_input(
            label="Select data folder",
            key="page_1_exp_data_folder_text_input",
            help="Select NMR experiment data folder"
        )
        expno = st.number_input(
            label="Enter Expno",
            key="page_1_expno_number_input"
        )
        procno = st.number_input(
            label="Enter Procno",
            key="page_1_procno_number_input"
        )

    with st.container():
        st.write("Handle Analysis parameters")
        st.selectbox(
            label="Analysis type",
            options=["Option A", "Option B"]
        )

    clustering = st.form_submit_button("Clustering")

    if clustering:
        map_all_options_to_session_state()  # See utils for more info
        st.session_state.pages["Page_2"] = True
