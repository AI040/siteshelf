from app.services.file_parser import parse_upload
from app.services.validation import validate_websites
from tests.conftest import make_csv


def run(rows):
    return validate_websites(parse_upload(make_csv(rows), "x.csv"))


def test_valid_rows_get_ids_and_uppercase_type():
    result = run([["Sequoia", "sequoiacap.com", "vc", "USA"]])
    assert len(result.valid) == 1
    assert result.rejected.empty
    row = result.valid.iloc[0]
    assert len(row["website_id"]) == 32
    assert row["website_type"] == "VC"


def test_invalid_type_is_rejected_with_reason_and_file_row():
    result = run([
        ["Good", "good.com", "VC", "IN"],
        ["Bad", "bad.com", "XYZ", "IN"],
    ])
    assert len(result.valid) == 1
    assert len(result.rejected) == 1
    rejected = result.rejected.iloc[0]
    assert rejected["file_row"] == 3  # header is row 1, "Bad" is the 2nd data row
    assert "invalid website type" in rejected["reason"]


def test_missing_fields_are_rejected():
    result = run([
        ["", "a.com", "VC", "IN"],
        ["B", "", "VC", "IN"],
        ["C", "c.com", "", "IN"],
    ])
    assert result.valid.empty
    reasons = list(result.rejected["reason"])
    assert reasons[0] == "missing website name"
    assert reasons[1] == "missing website link"
    assert reasons[2] == "missing website type"


def test_multiple_problems_are_all_listed():
    result = run([["", "nodots", "ZZZ", "IN"]])
    reason = result.rejected.iloc[0]["reason"]
    assert "missing website name" in reason
    assert "invalid website type" in reason
    assert "invalid website link" in reason
    assert reason.count(";") == 2


def test_link_without_a_domain_is_rejected():
    result = run([["Local", "localhost", "VC", "IN"]])
    assert "invalid website link" in result.rejected.iloc[0]["reason"]


def test_duplicates_in_file_are_collapsed_last_one_wins():
    result = run([
        ["First", "https://www.sequoiacap.com/", "VC", "USA"],
        ["Other", "kkr.com", "PE", "USA"],
        ["Last", "SequoiaCap.com", "VC", "India"],
    ])
    assert len(result.valid) == 2
    assert result.duplicates_removed == 1
    sequoia = result.valid[result.valid["website_link"].str.contains("equoia", case=False)]
    assert sequoia.iloc[0]["website_name"] == "Last"
    assert sequoia.iloc[0]["country"] == "India"


def test_rejected_rows_do_not_count_as_duplicates():
    result = run([
        ["A", "a.com", "VC", "IN"],
        ["A again", "a.com", "BAD", "IN"],
    ])
    assert len(result.valid) == 1
    assert result.duplicates_removed == 0
    assert len(result.rejected) == 1


def test_country_is_free_text_and_optional():
    result = run([
        ["A", "a.com", "VC", "United States"],
        ["B", "b.com", "VC", ""],
    ])
    assert result.rejected.empty
    countries = set(result.valid["country"].dropna())
    assert countries == {"United States"}


def test_overlong_country_rejected():
    result = run([["A", "a.com", "VC", "x" * 101]])
    assert "country too long" in result.rejected.iloc[0]["reason"]


def test_valid_rows_sorted_by_id():
    result = run([[f"S{i}", f"site{i}.com", "VC", "IN"] for i in range(20)])
    ids = list(result.valid["website_id"])
    assert ids == sorted(ids)
