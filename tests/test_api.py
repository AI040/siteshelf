"""API tests. Need fastapi + httpx, and TEST_DATABASE_URL for the upload tests."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import get_db_session  # noqa: E402
from app.main import create_app  # noqa: E402
from tests.conftest import make_csv  # noqa: E402

ROWS = [
    ["Sequoia", "sequoiacap.com", "VC", "USA"],
    ["Bad", "bad.com", "NOPE", "USA"],
]


@pytest.fixture
def client(pg_engine):
    from sqlalchemy.orm import Session

    app = create_app()

    def override():
        with Session(pg_engine, expire_on_commit=False) as s:
            yield s

    app.dependency_overrides[get_db_session] = override
    return TestClient(app)


def post(client, content, name="sites.csv"):
    return client.post("/api/v1/websites/upload", files={"file": (name, content, "text/csv")})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/health/db").status_code == 200


def test_upload_returns_counts_and_rejected_rows(client):
    res = post(client, make_csv(ROWS))
    assert res.status_code == 200
    body = res.json()
    assert (body["inserted"], body["existing"], body["rejected"]) == (1, 0, 1)
    assert body["rejected_rows"][0]["file_row"] == 3
    assert "invalid website type" in body["rejected_rows"][0]["reason"]

    again = post(client, make_csv(ROWS)).json()
    assert (again["inserted"], again["existing"]) == (0, 1)


def test_wrong_extension_is_400(client):
    res = post(client, b"hello", name="notes.txt")
    assert res.status_code == 400


def test_missing_columns_is_400_with_message(client):
    res = post(client, make_csv([["A", "VC"]], header=("website name", "website type")))
    assert res.status_code == 400
    assert "website link" in res.json()["detail"]
