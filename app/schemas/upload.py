"""Pydantic schemas for the upload API."""

from pydantic import BaseModel


class RejectedRow(BaseModel):
    file_row: int
    website_name: str | None = None
    website_link: str | None = None
    website_type: str | None = None
    country: str | None = None
    reason: str


class UploadResponse(BaseModel):
    rows_in_file: int
    duplicates_in_file: int
    inserted: int
    existing: int
    rejected: int
    rejected_rows: list[RejectedRow]
    rejected_rows_truncated: bool
