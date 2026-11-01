"""Orchestrates an upload: parse -> validate -> upsert -> commit."""

import logging
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import DatabaseError
from app.repositories import website_repository
from app.services.file_parser import parse_upload
from app.services.validation import validate_websites

logger = logging.getLogger(__name__)

DB_COLUMNS = ["website_id", "website_name", "website_link", "website_type", "country"]


@dataclass(frozen=True)
class UploadOutcome:
    rows_in_file: int
    duplicates_in_file: int
    inserted: int
    existing: int
    rejected: pd.DataFrame  # full table of rejected rows with reasons


def read_upload(content: bytes, filename: str) -> pd.DataFrame:
    """Parse a file without touching the database (used for previews)."""
    return parse_upload(content, filename)


def import_dataframe(session: Session, df: pd.DataFrame) -> UploadOutcome:
    """Validate a parsed DataFrame and upsert the valid rows in one transaction."""
    result = validate_websites(df)
    records = _to_records(result.valid)

    try:
        inserted, existing = website_repository.upsert_many(
            session, records, batch_size=get_settings().upsert_batch_size
        )
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        logger.exception("Upsert failed")
        raise DatabaseError() from exc

    logger.info(
        "Upload done: rows=%s inserted=%s existing=%s duplicates=%s rejected=%s",
        len(df), inserted, existing, result.duplicates_removed, len(result.rejected),
    )
    return UploadOutcome(
        rows_in_file=len(df),
        duplicates_in_file=result.duplicates_removed,
        inserted=inserted,
        existing=existing,
        rejected=result.rejected,
    )


def import_upload(session: Session, content: bytes, filename: str) -> UploadOutcome:
    """Parse raw file bytes and import them (used by the API)."""
    return import_dataframe(session, parse_upload(content, filename))


def _to_records(valid: pd.DataFrame) -> list[dict]:
    frame = valid[DB_COLUMNS].astype(object)
    return frame.where(frame.notna(), None).to_dict("records")
