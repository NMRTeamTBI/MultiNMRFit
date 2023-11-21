import streamlit as st
from sess_i.base.main import SessI

session_clustering  = SessI(st.session_state, "clustering")
session_io          = SessI(st.session_state, "inputs_outputs")

st.write(session_clustering)
st.write(session_io.widget_space["input_exp_data_path"])
    
# if not st.session_state.pages["Page_2"]:
#     st.header("Please finish with page 1")
# else:
#     st.header("Use this section to initialize fitting parameters")
#     threshold = st.number_input(
#         label="Enter threshold for ...."
    # )