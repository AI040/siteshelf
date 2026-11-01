"""Shared fixtures.

Pure-logic tests (urls, parser, validation) need nothing special.
Database tests need a PostgreSQL URL in TEST_DATABASE_URL, e.g.

    TEST_DATABASE_URL=postgresql://postgres:pw@localhost:5432/postgres pytest

Each run creates its own throw-away schema and drops it afterwards, so it is
safe to point at a normal database (your real tables are never touched).
"""

import io
import os
import uuid

import pandas as pd
import pytest


@pytest.fixture(autouse=True)
def fresh_settings():
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_csv(rows: list[list[str]], header=("website name", "website link", "website type", "country")) -> bytes:
    df = pd.DataFrame(rows, columns=list(header))
    return df.to_csv(index=False).encode("utf-8")


def make_xlsx(rows: list[list[str]], header=("website name", "website link", "website type", "country")) -> bytes:
    buffer = io.BytesIO()
    pd.DataFrame(rows, columns=list(header)).to_excel(buffer, index=False)
    return buffer.getvalue()


@pytest.fixture
def pg_engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run database tests")
    pytest.importorskip("sqlalchemy")
    from sqlalchemy import create_engine, text

    import app.models  # noqa: F401
    from app.core.database import Base

    schema = f"test_{uuid.uuid4().hex[:8]}"
    admin = create_engine(url)
    with admin.begin() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    Base.metadata.create_all(engine)
    yield engine

    engine.dispose()
    with admin.begin() as conn:
        conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    admin.dispose()


@pytest.fixture
def session(pg_engine):
    from sqlalchemy.orm import Session

    with Session(pg_engine, expire_on_commit=False) as s:
        yield s
