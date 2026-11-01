"""Row-level validation and de-duplication of parsed website data."""

from dataclasses import dataclass

import pandas as pd

from app.core.constants import WEBSITE_TYPES
from app.services.file_parser import OUTPUT_COLUMNS
from app.utils.urls import has_valid_host, make_website_id

MAX_NAME_LEN = 255
MAX_LINK_LEN = 2048
MAX_COUNTRY_LEN = 100


@dataclass(frozen=True)
class ValidationResult:
    valid: pd.DataFrame  # unique rows, with website_id, sorted by website_id
    rejected: pd.DataFrame  # file_row, the four columns, reason
    duplicates_removed: int


def _as_bool(mask: pd.Series) -> pd.Series:
    return mask.fillna(False).astype(bool)


def validate_websites(df: pd.DataFrame) -> ValidationResult:
    df = df.copy()
    df["website_type"] = df["website_type"].str.upper()

    types_text = ", ".join(WEBSITE_TYPES)
    checks = {
        "missing website name": df["website_name"].isna(),
        "missing website link": df["website_link"].isna(),
        "missing website type": df["website_type"].isna(),
        f"invalid website type (use {types_text})": (
            df["website_type"].notna() & ~df["website_type"].isin(WEBSITE_TYPES)
        ),
        "invalid website link": (
            df["website_link"].notna() & ~df["website_link"].map(has_valid_host).astype(bool)
        ),
        f"website name too long (max {MAX_NAME_LEN})": (
            df["website_name"].str.len() > MAX_NAME_LEN
        ),
        f"website link too long (max {MAX_LINK_LEN})": (
            df["website_link"].str.len() > MAX_LINK_LEN
        ),
        f"country too long (max {MAX_COUNTRY_LEN})": (
            df["country"].str.len() > MAX_COUNTRY_LEN
        ),
    }

    reason = pd.Series("", index=df.index, dtype="object")
    for text, mask in checks.items():
        mask = _as_bool(mask)
        separator = reason.where(reason == "", reason + "; ")
        reason = reason.where(~mask, separator + text)

    bad = reason != ""

    rejected = df.loc[bad, OUTPUT_COLUMNS].copy()
    rejected.insert(0, "file_row", rejected.index + 2)  # +2: header is row 1
    rejected["reason"] = reason[bad]

    valid = df.loc[~bad, OUTPUT_COLUMNS].copy()
    valid["website_id"] = valid["website_link"].map(make_website_id)

    # Collapse duplicates inside the file (last occurrence wins). Required:
    # a single INSERT ... ON CONFLICT cannot affect the same row twice.
    before = len(valid)
    valid = valid.drop_duplicates(subset="website_id", keep="last")
    duplicates_removed = before - len(valid)

    # Stable order -> consistent row-lock order if two uploads overlap
    valid = valid.sort_values("website_id")

    return ValidationResult(valid, rejected, duplicates_removed)
