from pathlib import Path 
import streamlit as st
import pandas as pd
from typing import Dict
import plotly.express as px
import os
from os import listdir
from os.path import isfile, join

@st.cache(allow_output_mutation=True)
def get_static_store() -> Dict:
    """This dictionary is initialized once and can be used to store the files uploaded"""
    return {}

def file_selector(folder_path):
    filenames = os.listdir(folder_path)
    selected_filename = st.selectbox('Select a file', filenames)
    return os.path.join(folder_path, selected_filename)

def main():
    fileslist = get_static_store()
    folderPath = st.text_input('Enter folder path:')
    if folderPath:    
        onlyfiles = [f for f in listdir(folderPath) if isfile(join(folderPath, f))]
        onlyfiles_fit = [f for f in onlyfiles if f.endswith('_fit.txt')]

        file = st.sidebar.selectbox("Select a file:",onlyfiles_fit)
        df = pd.read_csv(Path(folderPath,str(file)),sep='\t')
        param_list = list(df.columns)[3:]
        params = st.sidebar.selectbox("Select a parameter:",param_list)

        # st.header(file)

        fig = px.line(df, 
            x = "exp_no" if 1 is df.row_id.unique() else 'row_id', 
            y = params,
            )
        st.plotly_chart(fig)


main()


# def Vizualisation_App(args):
#     cluster_list = getList(d_id)
#     m_fname_list =[]

#     for i in cluster_list:
#         _multiplet_type_, mutliplet_results, mutliplet_stats = build_output(d_id[i], x_fit, fit_results, stat_results, scaling_factor, spectra_to_fit, offset)
#         # update results file if already exists
#         fname = Path(output_path,output_folder,output_name+'_'+str(_multiplet_type_)+'_'+str(i)+'_fit.txt')
#         m_fname = output_name+'_'+str(_multiplet_type_)+'_'+str(i)+'_fit'
#         m_fname_list.append(str(m_fname))

#     file = st.sidebar.selectbox("Select a file:",m_fname_list)
#     df = pd.read_csv(Path(output_path,output_folder,str(file)+'.txt'),sep='\t')

