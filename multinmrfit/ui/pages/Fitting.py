import streamlit as st
from sess_i.base.main import SessI


st.set_page_config(page_title="Fitting",layout="wide")
st.title("Fitting")

session = SessI(
    session_state = st.session_state,
    page="Fitting"
)

process = session.get_object(key="process")   

if session.object_space["steps_to_show"]["fit_ref"]:
    with st.form("Fit reference spectrum"):
        st.write("### Parameters")
        parameters = st.data_editor(
            process.ref_spectrum.params,
                hide_index=True,
                disabled=["signal_id", "model", "par", "opt", "opt_sd", "integral"],
                column_config={"opt":None, "opt_sd":None, "integral":None}
                )
        
        fit_ok = st.form_submit_button("Fit reference spectrum") 
else:

    st.write("Please define clusters...")
  

if fit_ok:

    # update parameters
    process.update_params(parameters)

    with st.form("fit all spectra"):

       

        # fit reference spectrum
        process.fit_reference_spectrum()

        # plot fit results
        fig = process.ref_spectrum.plot(ini=True, fit=True)
        fig.update_layout(autosize=False, width=900, height=900)
        st.plotly_chart(fig)

        p2 = st.data_editor(
            process.ref_spectrum.params,
                hide_index=True,
                column_config={"ini":None, "lb":None, "ub":None},
                disabled=True
                )

        fit_all = st.form_submit_button("Fit all spectra") 

        list_of_spectra = [2,3]


    #results = process.fit_from_ref(sp, dataset, signals, list_of_spectra)

# with st.expander(label="test", expanded=True):
# cluster_to_update = st.selectbox(
#     label='cluster',
#     options=list(signals.keys())
#     )

# session.register_widgets({"cluster_to_update":cluster_to_update})

# # st.write(session.widget_space["cluster_to_update"])

# edited_peak_table = st.data_editor(
#         pd.DataFrame.from_dict(signals[session.widget_space["cluster_to_update"]]['par'],orient='index'),
#         # column_config={
#         #     "ppm":"peak position",
#         #     "intensity":"peak intensity",
#         #     "cID":"cluster ID"
#         # },
#         hide_index=False
#         )
# available_models = utils.get_models()
# st.write(signals)
# sp.build_model(signals=signals, available_models=available_models)
# sp.fit()
# st.write(sp.params)
# fig = sp.plot(ini=True, fit=True)
# fig.update_layout(autosize=False, width=900, height=900)
# st.plotly_chart(fig)

# st.write(signals)

# if fitting:
#     with st.expander("test", expanded=True):
#         st.write(session.widget_space['user_models'])
#         st.write('##')
#     with st.expander("Fitting the reference spectrum", expanded=True): 
#         st.write(edited_peak_table)
#         available_models = io.IoHandler.get_models()
#         signals = {"singlet_TSP": {"model":"singlet", "par": {"x0": {"ini":0.0, "lb":-0.05, "ub":0.05}}}}
#         sp.build_model(signals=signals, available_models=available_models)

#         sp.fit()
#         fig = sp.plot(ini=True, fit=True)
#         fig.update_layout(autosize=False, width=900, height=900)
#         st.plotly_chart(fig)

