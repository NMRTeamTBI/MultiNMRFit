import streamlit as st

if not st.session_state.pages["Page_4"]:
    st.header("Please finish with page 3")
else:
    st.write("Page 4")