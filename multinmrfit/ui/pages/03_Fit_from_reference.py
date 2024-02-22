import streamlit as st
from sess_i.base.main import SessI


st.set_page_config(page_title="Fit from a spectrum of reference", layout="wide")
st.title("Fit from a spectrum of reference")

session = SessI(
    session_state = st.session_state,
    page="Fitting"
)

process = session.get_object(key="process")

spectra_list = []

if process is None or len(process.results) == 0:

    st.warning("Please process a spectrum used as reference.")

else:

    processed_regions = process.regions()

    col1, col2 = st.columns(2)
    with col1:
        region = st.selectbox(
                        label="Select region",
                        key="region_ref",
                        options=processed_regions,
                        index=0,
                        help="Select the number of the spectrum used for peak picking and clustering"
                        )
        spectra = process.spectra(region)
        compounds = process.compounds(rowno=None, region=region)
        st.info(f"Signal IDs: {compounds}")
        st.info(f"Processed spectra: {spectra}")

    with col2:


        reference_spectrum = st.selectbox(
                    label="Select spectrum used as reference",
                    key="reference_spectrum",
                    options=spectra,
                    index=0,
                    help="Select the number of the spectrum used for peak picking and clustering"
                    )
            
    # set default parameters
    spectra_to_process = "-".join([str(process.names[0]), str(process.names[-1])])


    spectra_to_process = st.text_input(
                label="Spectra to process",
                key="spectra_to_process",
                value=spectra_to_process,
                help="Enter all spectra to process"
                )
    
    reprocess = st.checkbox('Reprocess spectra already processed', value=session.widget_space["reprocess"], key="reprocess")

    session.register_widgets({
            "spectra_to_process": spectra_to_process,
            "reprocess":reprocess
        })
    
    with st.expander("Reference spectrum", expanded=False):
        fig = process.results[reference_spectrum][region].plot(ini=False, fit=True)
        fig.update_layout(autosize=False, width=800, height=600)
        fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15)) 
        st.plotly_chart(fig)
    
    spectra_list = process.build_spectra_list(spectra_to_process, ref=reference_spectrum, region=region, reprocess=reprocess)

    str_list = str(spectra_list) if len(spectra_list) else "None"
    st.info(f"Spectra to process: {str_list}")


if process is not None and len(spectra_list):

    stop = False

    col1, col2, col3 = st.columns(3)

    with col1:
        start = st.button("Fit selected spectra")
    
    if start and not stop:
        
        with col2:
            stop = st.empty()
            stop.button('Stop')
                    
        progress_text = "Operation in progress. Please wait."
        progress_bar = st.progress(0, text=progress_text)

        list_spectra_upper = [reference_spectrum] + sorted([i for i in spectra_list if i > reference_spectrum])
        list_spectra_lower = [reference_spectrum] + sorted([i for i in spectra_list if i < reference_spectrum], reverse=True)
            
        for i,j in enumerate(list_spectra_upper[1:]):
            percent_complete = (i+1)/(len(list_spectra_upper)+len(list_spectra_lower)-2)
            progress_text = f"Fitting spectrum {j} (using spectrum {list_spectra_upper[i]} as reference). Please wait."
            progress_bar.progress(percent_complete, text=progress_text)
            process.fit_from_ref(rowno=j, region=region, ref=list_spectra_upper[i])

        for i,j in enumerate(list_spectra_lower[1:]):
            percent_complete = (i+len(list_spectra_upper))/(len(list_spectra_upper)+len(list_spectra_lower)-2)
            progress_text = f"Fitting spectrum {j} (using spectrum {list_spectra_lower[i]} as reference). Please wait."
            progress_bar.progress(percent_complete, text=progress_text)
            process.fit_from_ref(rowno=j, region=region, ref=list_spectra_lower[i])

        progress_bar.empty()
        stop.empty()

        st.success("All spectra have been fitted.")
        
        process.save_process_to_file()



