import streamlit as st
from sess_i.base.main import SessI


st.set_page_config(page_title="Fit from a spectrum of reference", layout="wide")
st.title("Fit from a spectrum of reference")

session = SessI(session_state=st.session_state, page="Fitting")

process = session.get_object(key="process")
session.object_space["consolidate"] = True

def update_checkbox(widget):
    session.register_widgets({widget: not session.widget_space[widget]})

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

    if not session.widget_space["use_previous"]:
        session.register_widgets({"use_previous": True})

    use_previous = st.checkbox('Use initial values from best fit of previous spectrum', value=session.widget_space["use_previous"], key="use_previous")

    if not session.widget_space["use_DE"]:
        session.register_widgets({"use_DE": False})

    use_DE = st.checkbox('Refine initial values using Differential evolution', value=session.widget_space["use_DE"], key="use_DE")
                
    if session.widget_space["adapt_cnstr_wd"]:
        session.register_widgets({"adapt_cnstr_wd": True})

    if use_previous:
        adapt_cnstr_wd = st.checkbox('Adjust bounds dynamically', value=session.widget_space["adapt_cnstr_wd"], key="adapt_cnstr_wd", on_change=update_checkbox, args=["adapt_cnstr_wd"])
        if adapt_cnstr_wd:
            with st.container(border=True):
                df_cnstr_wd = st.data_editor(process.results[reference_spectrum][region].cnstr_wd,
                                             column_config={"relative": st.column_config.CheckboxColumn(
                                                 "relative",
                                                 help="Relative or absolute value of parameter change",
                                                 default=False)},
                                             disabled=["signal_id", "model", "par"],
                                             hide_index=True)
                update_cnstr_wd = st.button("Update bounds")
                if update_cnstr_wd:
                    process.results[reference_spectrum][region].cnstr_wd = df_cnstr_wd
    else:
        adapt_cnstr_wd = False

    session.register_widgets({
        "spectra_to_process": spectra_to_process,
        "reprocess": reprocess,
        "use_previous": use_previous,
        "adapt_cnstr_wd": adapt_cnstr_wd,
        "use_DE": use_DE
    })

    with st.expander("Reference spectrum", expanded=False):
        fig = process.results[reference_spectrum][region].plot(ini=False, fit=True)
        fig.update_layout(autosize=False, width=800, height=600)
        fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15))
        st.plotly_chart(fig, theme=None)

    spectra_list = process.build_spectra_list(spectra_to_process, ref=reference_spectrum, region=region, reprocess=reprocess)

    str_list = str(spectra_list) if len(spectra_list) else "None"
    st.info(f"Spectra to process: {str_list}")


if process is not None and len(spectra_list):

    stop = False
    method = "differential_evolution" if use_DE else "L-BFGS-B"

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

        cnstr_wd = process.results[reference_spectrum][region].cnstr_wd if adapt_cnstr_wd else None

        for i, j in enumerate(list_spectra_upper[1:]):
            percent_complete = (i+1)/(len(list_spectra_upper)+len(list_spectra_lower)-2)
            progress_text = f"Fitting spectrum {j} (using spectrum {list_spectra_upper[i]} as reference). Please wait."
            progress_bar.progress(percent_complete, text=progress_text)
            process.fit_from_ref(rowno=j, region=region, ref=list_spectra_upper[i], update_pars_from_previous=use_previous, update_cnstr_wd=cnstr_wd, method=method)

        for i, j in enumerate(list_spectra_lower[1:]):
            percent_complete = (i+len(list_spectra_upper))/(len(list_spectra_upper)+len(list_spectra_lower)-2)
            progress_text = f"Fitting spectrum {j} (using spectrum {list_spectra_lower[i]} as reference). Please wait."
            progress_bar.progress(percent_complete, text=progress_text)
            process.fit_from_ref(rowno=j, region=region, ref=list_spectra_lower[i], update_pars_from_previous=use_previous, update_cnstr_wd=cnstr_wd, method=method)

        progress_bar.empty()
        stop.empty()

        st.success("All spectra have been fitted.")

        process.save_process_to_file()
