""""
First page of the streamlit GUI for NmrFit. Contains logic for handling inputs, analysis, outputs and extra options.#

To launch streamlit:
    streamlit run "..\Inputs_&_Outputs.py"
"""

import streamlit as st
import multinmrfit
from sess_i.base.main import SessI

session = SessI(
    session_state = st.session_state,
    page = "inputs_outputs"
)

# set page title with multinmrfit version
st.set_page_config(page_title=f"multiNMRFit (v{multinmrfit.__version__})", layout="wide")
# st.set_page_config(layout="wide")
st.title(f"Welcome to multiNMRFit (v{multinmrfit.__version__})")

# store which processing steps have been done
if not session.object_space["steps_done"]:
    steps_done = {"clustering":False,
                "ref_fitted":False,
                "all_fitted":False}
    session.register_object(obj=steps_done, key="steps_done")

# set defaults
session.set_widget_defaults(
    input_exp_data_path = "C:/Users/millard/Documents/GIT/multinmrfit/data/",
    input_exp_data_folder = "8SD_enzyme300123",
    input_expno = 23,
    input_procno = 1,
    output_res_path = 'C:/Users/millard/Documents/GIT/multinmrfit/data/',
    output_res_folder = 'results_folder',
    output_res_filename = 'results_filename'
)

st.header("Use this section to handle inputs and outputs")

with st.form('Inputs/Outputs'):
    with st.container():
        st.write("## Inputs")
        input_exp_data_path = st.text_input(
            label="Enter data path",
            key = "input_exp_data_path",
            value = session.widget_space["input_exp_data_path"],
            help="Select NMR experiment data path"
        )
        input_exp_data_folder = st.text_input(
            label="Enter data folder",
            key = "input_exp_data_folder",
            value = session.widget_space["input_exp_data_folder"],
        )
        input_expno = st.number_input(
            label="Enter Expno",
            key="input_expno",  
            value = session.widget_space["input_expno"],
            help='Enter the expno(s) use in the analysis. If multiple numbers (separated with "," ) are provided it will automatically turned them into a list'
        )
        input_procno = st.number_input(
            label="Enter Procno",
            key="input_procno",  
            value = session.widget_space["input_procno"],
            help='Enter the procno. (Must be the same for all the experiments)'
        )
    with st.container():
        st.write("## Outputs")
        output_res_path = st.text_input(
            label="Enter output path",
            key="output_res_path",
            value = session.widget_space["output_res_path"],
        )
        output_res_folder = st.text_input(
            label="Enter output path",
            key="output_res_folder",
            value = session.widget_space["output_res_folder"],
        )
        output_res_filename = st.text_input(
            label="Enter output path",
            key="output_res_filename",
            value = session.widget_space["output_res_filename"],
        )

    submitted = st.form_submit_button('Submit')

if submitted:

    # update inputs & outputs
    session.register_widgets({
        "input_exp_data_path": input_exp_data_path,
        "input_exp_data_folder": input_exp_data_folder,
        "input_expno": input_expno,
        "input_procno": input_procno,
        "output_res_path": output_res_path,
        "output_res_folder": output_res_folder,
        "output_res_filename": output_res_filename
    })

    # reset previous processing steps (but not processing parameters)
    session.object_space["steps_done"]["clustering"] = False
    session.object_space["steps_done"]["ref_fitted"] = False
    session.object_space["steps_done"]["all_fitted"] = False


