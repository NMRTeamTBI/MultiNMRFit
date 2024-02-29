""""
First page of the streamlit GUI for NmrFit. Contains logic for handling inputs, analysis, outputs and extra options.#

To launch streamlit:
    streamlit run "../Inputs_&_Outputs.py"
"""

import streamlit as st
import multinmrfit
import pickle
import pathlib
from sess_i.base.main import SessI
from multinmrfit.base.process import Process
import pandas as pd


session = SessI(
    session_state = st.session_state,
    page = "inputs_outputs"
)

def save_defaults(options):
    save_path = pathlib.Path(multinmrfit.__file__).resolve().parent / "ui" / "conf"
    pathlib.Path(save_path).mkdir(parents=True, exist_ok=True)
    with open(str(save_path / 'default_conf.pickle'), 'wb') as handle:
        pickle.dump(options, handle, protocol=pickle.HIGHEST_PROTOCOL)

def load_defaults():
    try:
        load_path = pathlib.Path(multinmrfit.__file__).resolve().parent / "ui" / "conf" / 'default_conf.pickle'
        with open(str(load_path), 'rb') as handle:
            options = pickle.load(handle)

    except:
        options = {
                "analysis_type": 'pseudo2D',
                "output_res_path": "path/to/output/data",
                "output_res_folder": 'results_folder',
                "output_filename": "filename",
                "txt_data": None,
                "input_exp_data_path": "path/to/topspin/data/folder/", 
                "input_exp_data_folder": "dataset_name", 
                "input_expno": 1, 
                "input_procno": 1
            }

    session.set_widget_defaults(**options)
    return options

# set page title with multinmrfit version
st.set_page_config(page_title=f"multiNMRFit (v{multinmrfit.__version__})", layout="wide")
st.title(f"Welcome to multiNMRFit (v{multinmrfit.__version__})")


options = load_defaults()
uploaded_file = st.sidebar.file_uploader("Load a processing file.")

if uploaded_file is not None:
    
    # load process object
    with uploaded_file as file:
        #process = pd.read_pickle(file)
        process = pickle.load(file)
    
    # save in session state
    session.object_space["process"] = process

    # set wisgets defaults
    session.set_widget_defaults(
            analysis_type = process.analysis_type,
            input_exp_data_path = process.data_path,
            input_exp_data_folder = process.dataset,
            input_expno = process.expno,
            input_procno = process.procno,
            output_res_path = process.output_res_path,
            output_res_folder = process.output_res_folder,
            output_filename = process.filename,
            txt_data = process.txt_data if hasattr(process, 'txt_data') else None
        )

    # save state
    session.object_space["loaded_file"] = pathlib.Path(process.output_res_path, process.output_res_folder, process.filename + ".pkl")

reset_process = st.sidebar.button("Reset current process")

if reset_process:
    session.object_space["loaded_file"] = None
    process = None
    session.object_space["process"] = process
    options = load_defaults()

# show warning
if session.object_space["loaded_file"] is not None:
    st.info(f"Process file loaded: {session.object_space['loaded_file']}")
    st.warning("Warning: Remember to update paths below, otherwise the process file and the processing results will be silently overwritten.")

with st.container():
    st.write("### Data to process")
    disabled = False if session.object_space['process'] is None else True
    l_at = ['pseudo2D','list of 1Ds','txt data']
    analysis_type = st.selectbox(
            label='Select data type',
            key = 'analysis_type',
            options = l_at,
            index = l_at.index(session.widget_space["analysis_type"]) if session.widget_space["analysis_type"] is not None else 0,
            disabled=disabled
            )
    session.register_widgets({"analysis_type": analysis_type})

with st.form('Inputs/Outputs'):
    with st.container():
        st.write("### Inputs")
        if session.widget_space["analysis_type"] in ['pseudo2D','list of 1Ds']:
            input_exp_data_path = st.text_input(
                label="Enter data path",
                key = "input_exp_data_path",
                value = session.widget_space["input_exp_data_path"],
                help="Select NMR experiment data path",
                disabled=disabled
                )
            input_exp_data_folder = st.text_input(
                label="Enter data folder",
                key = "input_exp_data_folder",
                value = session.widget_space["input_exp_data_folder"],
                disabled=disabled
            )
            
            input_expno = st.text_input(
                label="Enter Expno",
                key="input_expno",  
                value = session.widget_space["input_expno"],
                disabled=disabled,
                help='Enter the expno(s) use in the analysis. If multiple numbers (separated with "," ) are provided it will automatically turned them into a list'
            )

            input_procno = st.number_input(
                label="Enter Procno",
                key="input_procno",  
                value = session.widget_space["input_procno"],
                disabled=disabled,
                help='Enter the procno. (Must be the same for all the experiments)'
            )
        
        if analysis_type == 'txt data':
            if disabled:
                st.write("File already loaded in current process.")
            else:
                txt_data = None
                txt_data_upl = st.file_uploader("Load a tsv file containing data.", type={"csv", "txt", "tsv"})
                if txt_data_upl is not None:
                    txt_data = pd.read_csv(txt_data_upl, sep="\t")
                session.object_space["txt_data"] = txt_data
           

    with st.container():
        st.write("### Outputs")
        output_res_path = st.text_input(
            label="Enter output path",
            key="output_res_path",
            value = session.widget_space["output_res_path"],
        )
        output_res_folder = st.text_input(
            label="Enter output folder",
            key="output_res_folder",
            value = session.widget_space["output_res_folder"],
        )
        output_filename = st.text_input(
            label="Enter filename",
            key="output_filename",
            value = session.widget_space["output_filename"],
        )

    if session.object_space["process"] is None:
        load_spectrum = st.form_submit_button('Load data')
    else:
        load_spectrum = st.form_submit_button('Update process')
    

if load_spectrum:
    # get input & output fields
    error = False
    options.update({
        "analysis_type": analysis_type,
        "output_res_path": output_res_path,
        "output_res_folder": output_res_folder,
        "output_filename": output_filename,
        "txt_data": txt_data if analysis_type == 'txt data' else None
    })
    if analysis_type in ['pseudo2D','list of 1Ds']:
        options.update({
            "input_exp_data_path": input_exp_data_path, 
            "input_exp_data_folder": input_exp_data_folder, 
            "input_expno": input_expno, 
            "input_procno": int(input_procno)
        })
    else:
        if txt_data is None:
            st.error("Please select a data file")
            error = True
 
    if not error:
        # save as defaults for next run
        save_defaults(options)

        # update inputs & outputs
        session.register_widgets(options)

        if session.object_space["process"] is None:
            # get dataset
            dataset = {
                    "analysis_type": str(options["analysis_type"]),
                    "data_path": str(options["input_exp_data_path"]) if analysis_type in ['pseudo2D','list of 1Ds'] else None,
                    "dataset": str(options["input_exp_data_folder"]) if analysis_type in ['pseudo2D','list of 1Ds'] else None,
                    "expno": str(options["input_expno"]) if analysis_type in ['pseudo2D','list of 1Ds'] else None,
                    "procno": str(options["input_procno"]) if analysis_type in ['pseudo2D','list of 1Ds'] else None,
                    "output_res_path": output_res_path,
                    "output_res_folder": output_res_folder,
                    "output_filename": output_filename,
                    "txt_data":options["txt_data"],
                    }
            # initialize process
            process = Process(dataset)
            # save in session state
            session.object_space["process"] = process

        else:
            # get process
            process = session.object_space["process"]
            # update process
            process.output_res_path = output_res_path
            process.output_res_folder = output_res_folder
            process.filename = output_filename
            
        session.set_widget_defaults(
                spectrum_limit_min = round(min(process.ppm_full), 2),
                spectrum_limit_max = round(max(process.ppm_full), 2)
                )

    
if session.object_space["process"] is not None:
    # show message
    st.success("Dataset loaded successfully.")