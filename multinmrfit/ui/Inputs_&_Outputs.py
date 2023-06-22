""""
First page of the streamlit GUI for NmrFit. Contains logic for handling inputs, analysis, outputs and extra options.#

To launch streamlit:
    streamlit run "..\Inputs_&_Outputs.py"
"""

import streamlit as st
import multinmrfit

from utils import directory_selector, map_all_options_to_session_state

# Configure page info
st.set_page_config(page_title=f"multiNMRFit (v{multinmrfit.__version__})")
st.title(f"Welcome to multiNMRFit (v{multinmrfit.__version__})")

# Initialize other pages
st.session_state.pages = {f"Page_{num}": False for num in range(1, 5)}
st.session_state.pages["Page_1"] = True

st.header("Use this section to handle inputs, outputs, analysis parameters and options")

# # Initialize config file uploader
# config_file = st.file_uploader(
#     label="Upload configuration file",
#     key="page_1_config_file_uploader",
#     help="Choose a configuration file to initialize the software with run parameters"
# )

# with st.expander(label="Input", expanded=True):
#     # Generate button to select the NMR data folder (Keys should be standardized)
#     data_folder_path = directory_selector(
#         message="Select NMR data directory",
#         button_key="page_1_data_path_selector",
#         path_key="input_directory"
#     )

# Generate form that will contain most of the page
input_form = st.form(key="page1_input_form")
# directory_selector("Select input data directory", "main_form_input_button", "input_directory")
with input_form:
    with st.container():
        st.write("## Inputs")

        # Add button to enter specific NMR experiment data folder name
        exp_data_path = st.text_input(
            label="Enter data path",
            key="page_1_exp_data_path_text_input",
            help="Select NMR experiment data path"
        )

        exp_data_folder = st.text_input(
            label="Enter data folder",
            key="page_1_exp_data_folder_text_input",
            help="Select NMR experiment data folder"
        )
        expno = st.number_input(
            label="Enter Expno",
            key="page_1_expno_number_input",
            help='Enter the expno(s) use in the analysis. If multiple numbers (separated with "," ) are provided it will automatically turned them into a list'
        )
        procno = st.number_input(
            label="Enter Procno",
            key="page_1_procno_number_input",
            help='Enter the procno. (Must be the same for all the experiments)'
        )

    with st.container():
        st.write("## Outputs")

        out_res_path = st.text_input(
            label="Enter output path",
            key="page_1_out_res_path_text_input",
            help="Select results data path"
        )

        out_res_folder = st.text_input(
            label="Enter data folder",
            key="page_1_out_res_folder_text_input",
            help="Select results data folder"
        )

        out_res_name = st.text_input(
            label="Enter name of the output files",
            key="page_1_out_res_name_text_input",
            help="Select a name that will be contained in all the results files"
        )

    with st.container():
        st.write("## Analysis parameters")
        st.selectbox(
            label="Analysis type",
            key="page_1_analysis_type",
            options=["Pseudo2D", "1D Series"]
        )

        ref_spec = st.number_input(
            label="Reference spectrum",
            key="page_1_ref_spe",
            help='Spectrum used as a starting point for the analysis'
        )

        col1, col2 = st.columns(2)

        with col1:
            spec_lim_max = st.number_input(
                label="Spectral limits (max)",
                key="page_1_max_spec_lim",
                )
            
        with col2:
            spec_lim_min = st.number_input(
                label="Spectral limits (min)",
                key="page_1_min_spec_lim",
                )

    with st.container():
        st.write("## Options")

        #Comments for Loic : is this possible? Open the number input only if check box checked?
        part_proc =st.checkbox(
            label='Partial processing of a pseudo2D experiment',
            help='For partial processing of Pseudo2D experiment'
        )
        if part_proc:
            row_no = st.number_input(
                label="Row number",
                key="page_1_opt_data_row_num",
                help='Provide a list of rows '
            )

        pre_fit = st.checkbox(
            label='Use previous fit',
            key="page_1_opt_prev_fit",
            help='Use the parameters of the previous fit as starting parameters for the following one'
        )

        offset = st.checkbox(
            label='Add an offset',
            key="page_1_opt_offset",
            help='Include a linear offset to the fitting procedure'
        )

        verbose_log = st.checkbox(
            label='Verbose log',
            key="page_1_opt_veb_log",
            help='Include Verbose log'
        )

        merge_pdf = st.checkbox(
            label='Merge pdf(s)',
            key="page_1_opt_merge_pdf",
            help='Merge all pdf plot in a single one'
        )

    clustering = st.form_submit_button("Clustering")

    if clustering:
        map_all_options_to_session_state()  # See utils for more info
        st.session_state.pages["Page_2"] = True
