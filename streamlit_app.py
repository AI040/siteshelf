"""Streamlit entry point.

Run:  streamlit run streamlit_app.py
(Kept at the project root so `app` and `ui` are importable.)
"""

import streamlit as st

from app.core.config import get_settings

# Must be the first Streamlit command
st.set_page_config(page_title=get_settings().app_name, page_icon="📥", layout="centered")

from ui.upload_page import render  # noqa: E402

render()
