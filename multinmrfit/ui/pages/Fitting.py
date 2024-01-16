import streamlit as st
import pandas as pd
from sess_i.base.main import SessI


st.set_page_config(page_title="Fitting",layout="wide")
st.title("Fitting")

session = SessI(
    session_state = st.session_state,
    page="Fitting"
)

process = session.get_object(key="process")   

if session.object_space["steps_to_show"]["fit_all"]:
    # set default parameters

    spectra_to_process = st.text_input(
            label="Spectra to process",
            key="spectra_to_process",
            value="-".join([str(process.spectra_list[0]), str(process.spectra_list[-1])]),
            help="Enter all spectra to process"
            )

    spectra_list = process.update_spectra_list(spectra_to_process)

    st.write(f"Spectra to process: {spectra_list}")
    st.write(f"Reference: {process.ref_spectrum_rowno}")

else:

    st.write("Please process reference spectrum...")


with st.form("fit all spectra"):

    fit_all = st.form_submit_button("Fit all spectra") 

    if fit_all:

        progress_text = "Operation in progress. Please wait."
        progress_bar = st.progress(0, text=progress_text)

        process.spectra_list = spectra_list

        list_spectra_upper = [process.ref_spectrum_rowno] + sorted([i for i in spectra_list if i > process.ref_spectrum_rowno])
        list_spectra_lower = [process.ref_spectrum_rowno] + sorted([i for i in spectra_list if i < process.ref_spectrum_rowno], reverse=True)
        
        for i,j in enumerate(list_spectra_upper[1:]):
            process.fit_from_ref(rowno=j, ref=list_spectra_upper[i])
            percent_complete = (i+1)/(len(list_spectra_upper)+len(list_spectra_lower)-2)
            progress_bar.progress(percent_complete, text=progress_text)

        for i,j in enumerate(list_spectra_lower[1:]):
            process.fit_from_ref(rowno=j, ref=list_spectra_lower[i])
            percent_complete = (i+len(list_spectra_upper))/(len(list_spectra_upper)+len(list_spectra_lower)-2)
            progress_bar.progress(percent_complete, text=progress_text)

        progress_bar.empty()
        st.success("Done.")

        for k, v in process.results.items():
            st.write(f"rowno: {k}")
            fig = v.plot(ini=True, fit=True)
            fig.update_layout(autosize=False, width=800, height=600)
            fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15)) 
            st.plotly_chart(fig)
        
    
