"""Verify that the existing database target is accessible.

This application must not create or alter database objects. The expected
PostgreSQL target is website.website_info.

    python -m app.core.init_db
"""

import app.models  # noqa: F401  (registers the ORM model)
from sqlalchemy import inspect

from app.core.database import get_engine


def init_db() -> None:
    engine = get_engine()
    inspector = inspect(engine)
    if "website" not in inspector.get_schema_names():
        raise RuntimeError("Required PostgreSQL schema 'website' does not exist")
    if not inspector.has_table("website_info", schema="website"):
        raise RuntimeError("Required table 'website.website_info' does not exist")


if __name__ == "__main__":
    init_db()
    print("Verified existing database target: website.website_info")
