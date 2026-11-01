"""Read an uploaded CSV / Excel file into a clean DataFrame."""

import io
import re
from pathlib import Path

import pandas as pd

from app.core.config import get_settings
from app.core.exceptions import FileParseError, FileTooLargeError, MissingColumnsError

ALLOWED_SUFFIXES = {".xlsx", ".xls", ".csv"}

# Header names are matched loosely: case, spaces and underscores are ignored.
COLUMN_ALIASES = {
    "website name": "website_name",
    "website link": "website_link",
    "website type": "website_type",
    "country": "country",
    "country code": "country",  # older files
}
REQUIRED_COLUMNS = ["website_name", "website_link", "website_type"]
OUTPUT_COLUMNS = ["website_name", "website_link", "website_type", "country"]
EXPECTED_HEADERS = "website name, website link, website type, country"


def parse_upload(content: bytes, filename: str) -> pd.DataFrame:
    """Parse raw file bytes into a DataFrame with the four expected columns.

    The DataFrame index is kept as the original data-row position so that
    rejected rows can be traced back to a row number in the file.
    """
    if len(content) > get_settings().max_upload_bytes:
        raise FileTooLargeError(
            f"File is larger than the {get_settings().max_upload_mb} MB limit."
        )

    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise FileParseError("Please upload a .xlsx, .xls or .csv file.")

    try:
        if suffix == ".csv":
            df = _read_csv(content)
        else:
            df = pd.read_excel(io.BytesIO(content), dtype=str)
    except FileParseError:
        raise
    except Exception as exc:
        raise FileParseError(f"Could not read the file: {exc}") from exc

    return _normalize_frame(df)


def _read_csv(content: bytes) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(io.BytesIO(content), dtype=str, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise FileParseError("Could not decode the CSV file. Save it as UTF-8 and retry.")


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    # "Website_Name " -> "website name" -> website_name
    df.columns = [re.sub(r"[_\s]+", " ", str(c)).strip().lower() for c in df.columns]
    df = df.rename(columns=COLUMN_ALIASES)
    df = df.loc[:, ~df.columns.duplicated()]  # e.g. both "country" and "country code"

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        names = ", ".join(c.replace("_", " ") for c in missing)
        raise MissingColumnsError(
            f"Missing required column(s): {names}. Expected columns: {EXPECTED_HEADERS}."
        )
    if "country" not in df.columns:
        df["country"] = None

    df = df[OUTPUT_COLUMNS].dropna(how="all").copy()

    # Trim whitespace; empty strings become missing values
    for col in OUTPUT_COLUMNS:
        cleaned = df[col].astype("string").str.strip()
        df[col] = cleaned.where(cleaned.notna() & (cleaned != ""), pd.NA)

    if df.empty:
        raise FileParseError("The file has no data rows.")
    return df
