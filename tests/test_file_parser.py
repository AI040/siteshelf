import pandas as pd
import pytest

from app.core.exceptions import FileParseError, FileTooLargeError, MissingColumnsError
from app.services.file_parser import parse_upload
from tests.conftest import make_csv, make_xlsx

ROWS = [
    ["Sequoia", "sequoiacap.com", "VC", "USA"],
    ["KKR", "kkr.com", "PE", "USA"],
]


def test_parses_csv():
    df = parse_upload(make_csv(ROWS), "sites.csv")
    assert list(df.columns) == ["website_name", "website_link", "website_type", "country"]
    assert len(df) == 2
    assert df.iloc[0]["website_name"] == "Sequoia"


def test_parses_xlsx():
    df = parse_upload(make_xlsx(ROWS), "sites.xlsx")
    assert len(df) == 2
    assert df.iloc[1]["website_link"] == "kkr.com"


def test_headers_are_matched_loosely():
    content = make_csv(ROWS, header=("Website Name ", "WEBSITE_LINK", "website  type", "Country"))
    df = parse_upload(content, "x.csv")
    assert list(df.columns) == ["website_name", "website_link", "website_type", "country"]


def test_old_country_code_header_still_works():
    content = make_csv(ROWS, header=("website name", "website link", "website type", "country code"))
    df = parse_upload(content, "x.csv")
    assert df.iloc[0]["country"] == "USA"


def test_country_column_is_optional():
    content = make_csv([["A", "a.com", "VC"]], header=("website name", "website link", "website type"))
    df = parse_upload(content, "x.csv")
    assert pd.isna(df.iloc[0]["country"])


def test_missing_required_column_is_reported_by_name():
    content = make_csv([["A", "VC"]], header=("website name", "website type"))
    with pytest.raises(MissingColumnsError) as exc:
        parse_upload(content, "x.csv")
    assert "website link" in exc.value.message


def test_unsupported_extension():
    with pytest.raises(FileParseError):
        parse_upload(b"whatever", "notes.txt")


def test_whitespace_trimmed_and_blanks_become_missing():
    df = parse_upload(make_csv([["  A  ", " a.com ", " vc ", "   "]]), "x.csv")
    assert df.iloc[0]["website_name"] == "A"
    assert df.iloc[0]["website_link"] == "a.com"
    assert pd.isna(df.iloc[0]["country"])


def test_blank_rows_dropped_but_row_numbers_preserved():
    csv = b"website name,website link,website type,country\nA,a.com,VC,IN\n,,,\nB,b.com,PE,IN\n"
    df = parse_upload(csv, "x.csv")
    assert len(df) == 2
    # second data row (index 1) was blank; "B" is still index 2 -> file row 4
    assert list(df.index) == [0, 2]


def test_file_with_no_data_rows():
    with pytest.raises(FileParseError):
        parse_upload(b"website name,website link,website type,country\n", "x.csv")


def test_garbage_excel_gives_friendly_error():
    with pytest.raises(FileParseError):
        parse_upload(b"this is not an excel file", "x.xlsx")


def test_csv_in_windows_encoding():
    csv = "website name,website link,website type,country\nCafé Capital,cafe.com,VC,France\n".encode("cp1252")
    df = parse_upload(csv, "x.csv")
    assert df.iloc[0]["website_name"] == "Café Capital"


def test_oversized_file_rejected(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    with pytest.raises(FileTooLargeError):
        parse_upload(make_csv(ROWS), "x.csv")
