import streamlit as st
from sess_i.base.main import SessI

import multinmrfit.ui.utils as utils

st.set_page_config(page_title="Fitting",layout="wide")
st.title("Fitting")

session = SessI(
    session_state = st.session_state,
    page="Fitting"
)

sp = st.session_state['Object_Space']['reference_spectrum']

utils = utils.IoHandler()
signals = utils.create_models(st.session_state["Global_Widget_Space"]["clustering"]['user_models'])
available_models = utils.get_models()
sp.build_model(signals=signals, available_models=available_models)
sp.fit()
fig = sp.plot(ini=True, fit=True)
fig.update_layout(autosize=False, width=900, height=900)
st.plotly_chart(fig)

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

