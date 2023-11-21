import streamlit as st

if not st.session_state.pages["Page_3"]:
    st.header("Please finish with page 2")
else:
    st.write("Page 3")