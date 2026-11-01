"""Streamlit entry point.

Run:  streamlit run streamlit_app.py
(Kept at the project root so `app` and `ui` are importable.)
"""

import os

import streamlit as st

from app.core.config import get_settings

# Streamlit Cloud secrets are not automatically read by the pydantic settings loader.
for key in (
    "DATABASE_URL",
    "LOG_LEVEL",
    "MAX_UPLOAD_MB",
    "UPSERT_BATCH_SIZE",
    "REJECTED_PREVIEW_LIMIT",
):
    try:
        if key not in os.environ and key in st.secrets:
            os.environ[key] = str(st.secrets[key])
    except Exception:
        break

# Must be the first Streamlit command
st.set_page_config(page_title=get_settings().app_name, page_icon="📥", layout="centered")

from ui.upload_page import render  # noqa: E402

render()
