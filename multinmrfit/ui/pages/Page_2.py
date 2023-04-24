import streamlit as st

if not st.session_state.pages["Page_2"]:
    st.header("Please finish with page 1")
else:
    st.header("Use this section to initialize fitting parameters")
    threshold = st.number_input(
        label="Enter threshold for ...."
    )