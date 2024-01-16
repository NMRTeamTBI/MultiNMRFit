import streamlit as st
from sess_i.base.main import SessI


st.set_page_config(page_title="Fitting",layout="wide")
st.title("Fitting")

session = SessI(
    session_state = st.session_state,
    page="Fitting"
)

if session.object_space["steps_to_show"]["fit_all"]:

    process = session.get_object(key="process")   

    col1, col2 = st.columns(2)

    with col1:
        already_processed = sorted(process.results.keys())
        reference_spectrum = st.selectbox(
                    label="Select reference spectrum",
                    key="reference_spectrum",
                    options=already_processed,
                    index=already_processed.index(process.ref_spectrum_rowno),
                    help="Select the number of the spectrum used for peak picking and clustering"
                    )
            
    with col2:
        spectra_to_process = st.text_input(
                label="Spectra to process",
                key="spectra_to_process",
                value="-".join([str(process.spectra_list[0]), str(process.spectra_list[-1])]),
                help="Enter all spectra to process"
                )

    with st.expander("Reference spectrum", expanded=False):
        fig = process.results[reference_spectrum].plot(ini=False, fit=True)
        fig.update_layout(autosize=False, width=800, height=600)
        fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15)) 
        st.plotly_chart(fig)
    
    spectra_list = process.update_spectra_list(spectra_to_process)

    str_list = str(spectra_list) if len(spectra_list) else "None (wrong input)"
    st.write(f"spectra to process: {str_list}")

else:

    st.warning("Please process a spectrum used as reference.")
    

if session.object_space["steps_to_show"]["fit_all"] and len(spectra_list):

    stop = False

    col1, col2, col3 = st.columns(3)

    with col1:
        start = st.button("Fit selected spectra", key="start_button")
    
    if start and not stop:
        
        with col2:
            stop = st.button("Stop")

        progress_text = "Operation in progress. Please wait."
        progress_bar = st.progress(0, text=progress_text)

        list_spectra_upper = [reference_spectrum] + sorted([i for i in spectra_list if i > reference_spectrum])
        list_spectra_lower = [reference_spectrum] + sorted([i for i in spectra_list if i < reference_spectrum], reverse=True)
            
        for i,j in enumerate(list_spectra_upper[1:]):
            process.fit_from_ref(rowno=j, ref=list_spectra_upper[i])
            percent_complete = (i+1)/(len(list_spectra_upper)+len(list_spectra_lower)-2)
            progress_text = f"Fitting spectrum {j} (using spectrum {list_spectra_upper[i]} as reference). Please wait."
            progress_bar.progress(percent_complete, text=progress_text)

        for i,j in enumerate(list_spectra_lower[1:]):
            process.fit_from_ref(rowno=j, ref=list_spectra_lower[i])
            percent_complete = (i+len(list_spectra_upper))/(len(list_spectra_upper)+len(list_spectra_lower)-2)
            progress_text = f"Fitting spectrum {j} (using spectrum {list_spectra_upper[i]} as reference). Please wait."
            progress_bar.progress(percent_complete, text=progress_text)

        progress_bar.empty()
        st.success("Done.")

        session.object_space["steps_to_show"]["visu"] = True


