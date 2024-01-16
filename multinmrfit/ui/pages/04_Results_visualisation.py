import streamlit as st
import multinmrfit
from sess_i.base.main import SessI


session = SessI(
    session_state = st.session_state,
    page="Results visualization"
)

st.title("Results visualization")


if session.object_space["steps_to_show"]["visu"]:
    
    process = session.get_object(key="process")   


    for k, v in process.results.items():
        st.write(f"rowno: {k}")
        fig = v.plot(ini=True, fit=True)
        fig.update_layout(autosize=False, width=800, height=600)
        fig.update_layout(legend=dict(yanchor="top", xanchor="right", y=1.15)) 
        st.plotly_chart(fig)
            
    