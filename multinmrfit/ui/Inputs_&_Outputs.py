""""
First page of the streamlit GUI for NmrFit. Contains logic for handling inputs, analysis, outputs and extra options.#

To launch streamlit:
    streamlit run "..\Inputs_&_Outputs.py"
"""

import streamlit as st
import multinmrfit
import pickle
import pathlib
from sess_i.base.main import SessI

session = SessI(
    session_state = st.session_state,
    page = "inputs_outputs"
)

def save_defaults(options):
    save_path = pathlib.Path(multinmrfit.__file__).resolve().parent / "ui" / "conf"
    pathlib.Path(save_path).mkdir(parents=True, exist_ok=True)
    with open(save_path / 'default_conf.pickle', 'wb') as handle:
        pickle.dump(options, handle, protocol=pickle.HIGHEST_PROTOCOL)

def load_defaults():
    try:
        load_path = pathlib.Path(multinmrfit.__file__).resolve().parent / "ui" / "conf" / 'default_conf.pickle'
        with open(load_path, 'rb') as handle:
            options = pickle.load(handle)
        session.set_widget_defaults(
            input_exp_data_path = options["input_exp_data_path"],
            input_exp_data_folder = options["input_exp_data_folder"],
            input_expno = options["input_expno"],
            input_procno = options["input_procno"],
            output_res_path = options["output_res_path"],
            output_res_folder = options["output_res_folder"],
            output_res_filename = options["output_res_filename"]
        )
    except:
        session.set_widget_defaults(
            input_exp_data_path = "path/to/topspin/data/folder/",
            input_exp_data_folder = "dataset_name",
            input_expno = 1,
            input_procno = 1,
            output_res_path = "path/to/output/data",
            output_res_folder = 'results_folder',
            output_res_filename = 'results_filename'
        )

# set page title with multinmrfit version
st.set_page_config(page_title=f"multiNMRFit (v{multinmrfit.__version__})", layout="wide")
# st.set_page_config(layout="wide")
st.title(f"Welcome to multiNMRFit (v{multinmrfit.__version__})")

# store which processing steps have been done
if not session.object_space["steps_to_show"]:
    steps_to_show = {"clustering":False,
                     "fit_ref":False,
                     "fit_all":False}
    session.register_object(obj=steps_to_show, key="steps_to_show")

# set defaults
load_defaults()

with st.form('Inputs/Outputs'):
    with st.container():
        st.write("### Inputs")
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
        st.write("### Outputs")
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

    load_spectrum = st.form_submit_button('Load spectrum')

if load_spectrum:

    # get input & output fields
    options = {
        "input_exp_data_path": input_exp_data_path,
        "input_exp_data_folder": input_exp_data_folder,
        "input_expno": input_expno,
        "input_procno": input_procno,
        "output_res_path": output_res_path,
        "output_res_folder": output_res_folder,
        "output_res_filename": output_res_filename
    }

    # update inputs & outputs
    session.register_widgets(options)

    # save as defaults for next run
    save_defaults(options)

    # reset processing steps to show
    session.object_space["steps_to_show"]["clustering"] = True
    session.object_space["steps_to_show"]["fit_ref"] = False
    session.object_space["steps_to_show"]["fit_all"] = False
