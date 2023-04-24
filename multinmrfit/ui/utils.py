"""
Extra functions for building the streamlit GUI
"""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path

import streamlit as st


# Initialize a directory selector button
def directory_selector(message, button_key, path_key):
    # Set up tkinter for directory chooser
    root = tk.Tk()
    root.withdraw()

    # Make folder picker dialog appear on top of other windows
    root.wm_attributes('-topmost', 1)

    if not hasattr(st.session_state, "paths"):
        st.session_state.paths = {}

    # Initialize folder picker button and add logic
    clicked = st.button(
        message, key=button_key
    )
    if clicked:
        # Initialize path from directory selector and add
        # to session state paths dict
        st.session_state.paths[path_key] = Path(st.text_input(
            "Selected directory:",
            filedialog.askdirectory(master=root)
        ))
        if st.session_state.paths[path_key] == Path(".") or not st.session_state.paths[path_key].exists():
            raise RuntimeError("Please provide a valid path")

def map_all_options_to_session_state():
    """
    This function will serve to map all the widget states into a dictionnary in the session state so that when returning
    to a previous page widget states are reinstated and not lost
    """
    pass
