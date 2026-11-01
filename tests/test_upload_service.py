"""Database tests: need TEST_DATABASE_URL (see conftest.py)."""

import pytest

pytest.importorskip("sqlalchemy")

from sqlalchemy import select  # noqa: E402

from app.models import Website  # noqa: E402
from app.services import upload_service  # noqa: E402
from tests.conftest import make_csv  # noqa: E402

ROWS = [
    ["Sequoia", "https://www.sequoiacap.com/", "VC", "USA"],
    ["KKR", "kkr.com", "PE", "USA"],
]


def all_sites(session):
    return {w.website_link: w for w in session.scalars(select(Website))}


def test_new_sites_are_inserted(session):
    outcome = upload_service.import_upload(session, make_csv(ROWS), "x.csv")
    assert (outcome.inserted, outcome.existing) == (2, 0)
    sites = all_sites(session)
    assert len(sites) == 2
    seq = sites["https://www.sequoiacap.com/"]
    assert len(seq.website_id) == 32
    assert seq.created_at is not None and seq.updated_at is not None


def test_reupload_only_refreshes_updated_at(session):
    upload_service.import_upload(session, make_csv(ROWS), "x.csv")
    before = {k: (v.created_at, v.updated_at) for k, v in all_sites(session).items()}

    # Same sites, but with different name / type / country in the new file
    changed = [
        ["Sequoia RENAMED", "sequoiacap.com", "PE", "India"],
        ["KKR RENAMED", "https://kkr.com/", "VC", "UK"],
    ]
    session.expire_all()
    outcome = upload_service.import_upload(session, make_csv(changed), "x.csv")

    assert (outcome.inserted, outcome.existing) == (0, 2)
    session.expire_all()
    sites = list(session.scalars(select(Website)))
    assert len(sites) == 2  # no new rows
    for site in sites:
        created_before, updated_before = before[site.website_link]
        assert site.created_at == created_before
        assert site.updated_at > updated_before
        assert site.website_name in {"Sequoia", "KKR"}  # untouched
        assert site.country == "USA"


def test_mixed_new_and_existing(session):
    upload_service.import_upload(session, make_csv(ROWS), "x.csv")
    rows = ROWS + [["Accel", "accel.com", "VC", "UK"]]
    outcome = upload_service.import_upload(session, make_csv(rows), "x.csv")
    assert (outcome.inserted, outcome.existing) == (1, 2)


def test_duplicates_inside_one_file_insert_once(session):
    rows = [
        ["A", "a.com", "VC", "IN"],
        ["A copy", "https://www.a.com/", "VC", "IN"],
        ["A copy 2", "A.COM", "VC", "IN"],
    ]
    outcome = upload_service.import_upload(session, make_csv(rows), "x.csv")
    assert (outcome.inserted, outcome.existing, outcome.duplicates_in_file) == (1, 0, 2)
    assert len(all_sites(session)) == 1


def test_rejected_rows_are_not_loaded(session):
    rows = [["Good", "good.com", "VC", "IN"], ["Bad", "bad.com", "NOPE", "IN"]]
    outcome = upload_service.import_upload(session, make_csv(rows), "x.csv")
    assert outcome.inserted == 1
    assert len(outcome.rejected) == 1
    assert list(all_sites(session)) == ["good.com"]


def test_batching_handles_more_rows_than_batch_size(session, monkeypatch):
    monkeypatch.setenv("UPSERT_BATCH_SIZE", "7")
    rows = [[f"S{i}", f"site{i}.com", "VC", "IN"] for i in range(50)]
    outcome = upload_service.import_upload(session, make_csv(rows), "x.csv")
    assert outcome.inserted == 50
    again = upload_service.import_upload(session, make_csv(rows), "x.csv")
    assert (again.inserted, again.existing) == (0, 50)
