import streamlit as st
from sess_i.base.main import SessI
import numpy as np
import pandas as pd
import math

st.set_page_config(page_title="Process ref spectrum", layout="wide")
st.title("Process spectra")


session = SessI(
    session_state=st.session_state,
    page="Process ref. spectrum"
)

# get process
process = session.object_space["process"]
session.object_space["consolidate"] = True

def append_line(chem_shift, process, name):
    new_line = pd.DataFrame({"ppm": [chem_shift], "intensity": [process.get_current_intensity(chem_shift)], "cID": [name]})
    process.current_spectrum.edited_peak_table = pd.concat([process.current_spectrum.edited_peak_table, new_line])

def update_params(process, parameters):
    process.update_params(parameters)

if process is None:

    st.warning("Please load a dataset or import a process file.")

else:

    # set default parameters
    session.set_widget_defaults(
        reference_spectrum=process.current_spectrum.rowno,
        spectrum_limit_min=round(max([process.current_spectrum.ppm_limits[0], process.ppm_full.min()]), 3),
        spectrum_limit_max=round(min([process.current_spectrum.ppm_limits[1], process.ppm_full.max()]), 3)
    )

    # add widgets
    col1, col2 = st.columns(2)

    with col1:
        reference_spectrum = st.selectbox(
            label="Select spectrum to process",
            key="reference_spectrum",
            options=process.names,
            index=0,
            help="Select the spectrum used as reference for peak detection and clustering"
        )

    with col2:
        cur_lim = str(round(session.widget_space["spectrum_limit_min"], 3)) + " | " + str(round(session.widget_space["spectrum_limit_max"], 3))
        regs = ["Add new region"] + process.regions(reference_spectrum)
        idx = regs.index(cur_lim) if cur_lim in regs else 0

        region = st.selectbox(
            label="Select region to (re)process",
            key="regions",
            options=regs,
            index=idx,
            help="Select the region"
        )

    if region != "Add new region":
        exist = process.results.get(reference_spectrum, {}).get(region, False)
        if exist:
            _, _, col3, col4 = st.columns(4)
            with col3:
                delete = st.button("Delete in current spectrum", on_click=process.delete_region, args=[reference_spectrum, region])
            with col4:
                delete = st.button("Delete in all spectra", on_click=process.delete_region, args=[None, region])

    try:
        val_min, val_max = process.results[reference_spectrum][region].ppm_limits
        disabled = True
    except:
        val_min = round(process.current_spectrum.ppm_limits[0], 3)
        val_max = round(process.current_spectrum.ppm_limits[1], 3)
        disabled = False

    col1, col2 = st.columns(2)
    with col1:
        spec_lim_max = st.number_input(
            label="Spectral limits (max)",
            key="spectrum_limit_max",
            value=round(val_max, 3),
            min_value=round(process.ppm_full.min(), 3),
            max_value=round(process.ppm_full.max(), 3),
            disabled=disabled,
            format="%.3f"
        )

    with col2:
        spec_lim_min = st.number_input(
            label="Spectral limits (min)",
            key="spectrum_limit_min",
            value=round(val_min, 3),
            min_value=round(process.ppm_full.min(), 3),
            max_value=round(process.ppm_full.max(), 3),
            disabled=disabled,
            format="%.3f"
        )

    session.register_widgets({
        "reference_spectrum": reference_spectrum,
        "spectrum_limit_max": round(spec_lim_max, 3),
        "spectrum_limit_min": round(spec_lim_min, 3),
    })

    # update reference spectrum when widgets' values are changed
    ppm_step = 0.01
    if process.current_spectrum.rowno != reference_spectrum or np.abs(process.current_spectrum.ppm_limits[0]-spec_lim_min) > ppm_step or np.abs(process.current_spectrum.ppm_limits[1]-spec_lim_max) > ppm_step:
        if (spec_lim_max-spec_lim_min) < 0.025:
            st.error("Error: ppm max must be higher than ppm min.")
            cur_lim = None
        else:
            cur_lim = str(round(spec_lim_min, 3)) + " | " + str(round(spec_lim_max, 3))
            process.set_current_spectrum(session.widget_space["reference_spectrum"], window=(round(spec_lim_min, 3), round(spec_lim_max, 3)))

    with st.container(border=True):

        if process is not None and cur_lim is not None:

            st.write("### Peak picking & Clustering")

            val = max(process.current_spectrum.intensity) / \
                5 if process.current_spectrum.peakpicking_threshold is None else process.current_spectrum.peakpicking_threshold
            peakpicking_threshold = st.number_input(
                label="Peak picking threshold",
                key="peakpicking_threshold",
                value=val,
                step=1e5,
                help="Enter threshold used for peak detection"
            )

            if peakpicking_threshold != process.current_spectrum.peakpicking_threshold:
                process.update_pp_threshold(peakpicking_threshold)

            fig = process.current_spectrum.plot(pp=process.current_spectrum.edited_peak_table, threshold=process.current_spectrum.peakpicking_threshold)
            fig.update_layout(autosize=False, width=800, height=500)
            fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15))
            st.plotly_chart(fig, theme=None)

            col1, col2 = st.columns(2)

            with col1:
                st.write("Peak list")
                edited_peak_table = st.data_editor(
                    process.current_spectrum.edited_peak_table,
                    column_config={
                        "ppm": "peak position",
                        "intensity": "peak intensity",
                        "cID": "cluster ID"
                    },
                    hide_index=True
                )
            with col2:
                st.write("Add peak in peak list")
                col3, col4 = st.columns(2)
                with col3:
                    chem_shift = st.number_input(
                        label="Chemical shift",
                        min_value=spec_lim_min,
                        max_value=spec_lim_max,
                        format="%.3f"
                    )
                    name = st.text_input(
                        label="Signal name"
                    )
                    add_peak = st.button("Add peak", on_click=append_line, args=(chem_shift, process, name))
                with col4:
                    intensity = st.number_input(
                        label="Intensity",
                        value=process.get_current_intensity(chem_shift),
                        disabled=True
                    )

            create_models = st.button("Assign peaks")

            if create_models:
                process.current_spectrum.edited_peak_table = edited_peak_table
                process.current_spectrum.user_models = {}

    if isinstance(process.current_spectrum.edited_peak_table, pd.DataFrame):

        tmp = process.current_spectrum.edited_peak_table.dropna()
        tmp = tmp[~tmp['cID'].isin(["", None])]

        if len(tmp.cID.values.tolist()):

            with st.form("create model"):

                st.write("### Model construction")

                clusters_and_models = process.model_cluster_assignment()

                col1, col2 = st.columns(2)

                with col1:
                    st.write("Cluster ID")
                with col2:
                    st.write("Models")

                for key in clusters_and_models:

                    options = [i for i in clusters_and_models[key]['models']]

                    col1, col2 = st.columns(2)
                    with col1:
                        st.text_input(
                            label='label',
                            label_visibility='collapsed',
                            value=f"{key} ({clusters_and_models[key]['n']} peaks)",
                            disabled=True
                        )

                    with col2:
                        model = st.selectbox(
                            label='label',
                            label_visibility='collapsed',
                            options=options,
                            index=0,
                            key=f"Parameter_value_{key}"
                        )

                    process.current_spectrum.user_models[key] = {'n': clusters_and_models[key]['n'],
                                                                 'model': model,
                                                                 "model_idx": options.index(model)}

                offset_def = False if not len(process.current_spectrum.params) else (process.current_spectrum.offset not in [False, None])
                offset = st.checkbox('offset', value=offset_def)

                fitting = st.form_submit_button("Build model")

                if fitting:
                    offs = {} if offset else None
                    process.create_signals(process.current_spectrum.user_models, offset=offs)

    if isinstance(process.current_spectrum.params, pd.DataFrame):

        if len(process.current_spectrum.params):

            with st.container(border=True):

                st.write("### Fitting")

                st.write("Parameters")

                if 'opt' in process.current_spectrum.params.columns:
                    tmp = process.current_spectrum.params.style.apply(process.highlighter, axis=None)
                else:
                    tmp = process.current_spectrum.params

                parameters = st.data_editor(
                    tmp,
                    hide_index=True,
                    disabled=["signal_id", "model", "par", "opt", "opt_sd", "integral"]
                )

                upd_pars = st.button("Update parameters", on_click=update_params, args=(process, parameters))

                use_DE = st.checkbox('Refine initial values using Differential evolution', value=session.widget_space["use_DE"], key="use_DE")
                
                fit_ok = st.button("Fit spectrum")

                if fit_ok:

                    # fit reference spectrum
                    with st.spinner('Fitting in progress, please wait...'):
                        method = "differential_evolution" if use_DE else "L-BFGS-B"
                        process.current_spectrum.fit(method=method)

                # show spectrum
                if process.current_spectrum.fit_results is not None:

                    # plot fit results
                    fig = process.current_spectrum.plot(ini=True, fit=True)
                    fig.update_layout(autosize=False, width=800, height=600)
                    fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15))
                    st.plotly_chart(fig, theme=None)
                    st.success("Spectrum has been fitted.")

                else:

                    # plot without the fit
                    fig = process.current_spectrum.plot(ini=True, fit=False)
                    fig.update_layout(autosize=False, width=800, height=600)
                    fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15))
                    st.plotly_chart(fig, theme=None)


    if process.current_spectrum.fit_results is not None:

        txt = "Add current region"
        if process.current_spectrum.rowno in process.results.keys():
            if process.current_spectrum.region in process.results[process.current_spectrum.rowno].keys():
                txt = "Update current region"

        save = st.button(txt, on_click=process.add_region)

        if save:
            st.success("Region saved")
            # save as pickle file
            with st.spinner('Saving process file...'):
                process.save_process_to_file()

