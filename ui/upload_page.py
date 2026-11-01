"""Streamlit upload page. Talks to the same service layer as the API."""

import streamlit as st

from app.core.config import get_settings
from app.core.database import get_session_factory
from app.core.exceptions import AppError
from app.services import upload_service


def render() -> None:
    settings = get_settings()

    st.title("Upload websites")
    st.caption(
        "Expected columns: website name, website link, website type (VC / PE / HNI), country. "
        "New sites are added; sites already in the database only get a fresh updated_at."
    )

    file = st.file_uploader(
        "Drag and drop a file here, or browse",
        type=["xlsx", "xls", "csv"],
        help=f"Up to {settings.max_upload_mb} MB",
    )
    if file is None:
        return

    try:
        df = upload_service.read_upload(file.getvalue(), file.name)
    except AppError as exc:
        st.error(exc.message)
        return

    st.write(f"**{len(df):,} rows** found. Preview:")
    st.dataframe(df.head(10), hide_index=True)

    # Keep the result in session state so it survives reruns
    # (e.g. clicking the download button below).
    state_key = f"outcome:{file.file_id}"

    if st.button("Load into database", type="primary"):
        try:
            with st.spinner("Loading..."):
                with get_session_factory()() as session:
                    st.session_state[state_key] = upload_service.import_dataframe(session, df)
        except AppError as exc:
            st.error(exc.message)
            return

    outcome = st.session_state.get(state_key)
    if outcome is None:
        return

    st.success("Done")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("New", f"{outcome.inserted:,}")
    c2.metric("Already existed", f"{outcome.existing:,}")
    c3.metric("Duplicates in file", f"{outcome.duplicates_in_file:,}")
    c4.metric("Rejected", f"{len(outcome.rejected):,}")

    if not outcome.rejected.empty:
        st.warning("Some rows were rejected. Fix them and upload again.")
        st.dataframe(outcome.rejected, hide_index=True)
        st.download_button(
            "Download rejected rows",
            outcome.rejected.to_csv(index=False).encode("utf-8"),
            file_name="rejected_rows.csv",
            mime="text/csv",
        )
