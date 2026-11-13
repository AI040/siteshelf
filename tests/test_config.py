import pytest
from sqlalchemy.engine import make_url

from app.core.config import Settings


@pytest.mark.parametrize("scheme", ["postgresql", "postgres"])
def test_plain_postgres_url_uses_installed_psycopg2_driver(scheme):
    settings = Settings(
        database_url=(
            f"{scheme}://user:p%40ss@db.example.test/neondb"
            "?sslmode=require&channel_binding=require"
        )
    )

    url = make_url(settings.sqlalchemy_url)

    assert url.drivername == "postgresql+psycopg2"
    assert url.username == "user"
    assert url.password == "p@ss"
    assert url.host == "db.example.test"
    assert url.database == "neondb"
    assert url.query == {"sslmode": "require", "channel_binding": "require"}


def test_explicit_postgres_driver_is_preserved():
    settings = Settings(database_url="postgresql+psycopg2://user:pass@db.example.test/neondb")

    assert make_url(settings.sqlalchemy_url).drivername == "postgresql+psycopg2"
