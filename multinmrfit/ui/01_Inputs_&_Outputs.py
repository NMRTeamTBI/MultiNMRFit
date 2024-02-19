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
            analysis_type = options['analysis_type'],
            input_exp_data_path = options["input_exp_data_path"],
            input_exp_data_folder = options["input_exp_data_folder"],
            input_expno = options["input_expno"],
            input_procno = options["input_procno"],
            output_res_path = options["output_res_path"],
            output_res_folder = options["output_res_folder"],
            output_filename = options["output_filename"]
        )
    except:
        session.set_widget_defaults(
            analysis_type = 'pseudo2D',
            input_exp_data_path = "path/to/topspin/data/folder/",
            input_exp_data_folder = "dataset_name",
            input_expno = 1,
            input_procno = 1,
            output_res_path = "path/to/output/data",
            output_res_folder = 'results_folder',
            output_filename = "filename"
        )

# set page title with multinmrfit version
st.set_page_config(page_title=f"multiNMRFit (v{multinmrfit.__version__})", layout="wide")
st.title(f"Welcome to multiNMRFit (v{multinmrfit.__version__})")


load_defaults()

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
            output_filename = process.filename
        )
    
    # save state
    session.object_space["loaded_file"] = pathlib.Path(process.output_res_path, process.output_res_folder, process.filename + ".pkl")

reset_process = st.sidebar.button("Reset current process")

if reset_process:
    session.object_space["loaded_file"] = None
    process = None
    session.object_space["process"] = process
    load_defaults()

# show warning
if session.object_space["loaded_file"] is not None:
    st.info(f"Process file loaded: {session.object_space['loaded_file']}")
    st.warning("Warning: Remember to update paths below, otherwise the process file and the processing results will be silently overwritten.")


with st.form('Inputs/Outputs'):
    
    # with st.container():
    #     st.write('Analysis type')

    #     analysis_type = st.selectbox(
    #         label='Select type of analysis',
    #         key = 'analysis_type',
    #         index=0,
    #         options = ['pseudo2D','list of 1Ds','txt data']
    #         )

    # session.register_widgets({
    #     "analysis_type": analysis_type,
    # })

    # st.write(session.widget_space["analysis_type"])

    with st.container():
        st.write("### Inputs")


        input_exp_data_path = st.text_input(
            label="Enter data path",
            key = "input_exp_data_path",
            value = session.widget_space["input_exp_data_path"],
            help="Select NMR experiment data path",
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
        output_filename = st.text_input(
            label="Enter filename",
            key="output_filename",
            value = session.widget_space["output_filename"],
        )

    if session.object_space["loaded_file"] is None:
        load_spectrum = st.form_submit_button('Load spectrum')
    else:
        load_spectrum = st.form_submit_button('Update process')
       

if load_spectrum:

    # get input & output fields
    options = {
        "input_exp_data_path": input_exp_data_path,
        "input_exp_data_folder": input_exp_data_folder,
        "input_expno": input_expno,
        "input_procno": input_procno,
        "output_res_path": output_res_path,
        "output_res_folder": output_res_folder,
        "output_filename": output_filename
    }

    # save as defaults for next run
    save_defaults(options)

    # update inputs & outputs
    session.register_widgets(options)

    # get dataset
    dataset = {"data_path": str(options["input_exp_data_path"]),
            "dataset": str(options["input_exp_data_folder"]),
            "expno": str(options["input_expno"]),
            "procno": str(options["input_procno"]),
            "output_res_path": output_res_path,
            "output_res_folder": output_res_folder,
            "output_filename": output_filename
            }

    if session.object_space["loaded_file"] is None:
        # initialize process
        process = Process(dataset, window=None)
        # save in session state
        session.object_space["process"] = process
    else:
        # get process
        process = session.object_space["process"]
        # update process
        process.data_path = dataset["data_path"]
        process.dataset = dataset["dataset"]
        process.expno = dataset["expno"]
        process.procno = dataset["procno"]
        process.filename = dataset["output_filename"]
    
    # save as pickle file
    #process.save_process_to_file()


if session.object_space["process"] is not None:
    # show message
    st.success("Dataset loaded successfully.")
