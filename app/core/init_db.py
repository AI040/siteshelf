"""Create the required database schema and table if they do not exist.

Existing tables are left unchanged; this is not a schema migration.

    python -m app.core.init_db
"""

import app.models  # noqa: F401  (registers the ORM model)
from sqlalchemy import schema
from sqlalchemy.engine import Engine

from app.core.database import Base, get_engine


def init_db(engine: Engine | None = None) -> None:
    """Create the ``website`` schema and registered tables when missing."""
    engine = engine or get_engine()
    with engine.begin() as connection:
        connection.execute(schema.CreateSchema("website", if_not_exists=True))
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized: website.website_info is ready")
