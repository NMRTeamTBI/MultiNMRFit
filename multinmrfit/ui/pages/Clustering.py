import streamlit as st
from sess_i.base.main import SessI

session = SessI(st.session_state, "Clustering")
st.write(session.page)
    
# if not st.session_state.pages["Page_2"]:
#     st.header("Please finish with page 1")
# else:
#     st.header("Use this section to initialize fitting parameters")
#     threshold = st.number_input(
#         label="Enter threshold for ...."
    # )