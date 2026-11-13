from unittest.mock import MagicMock, patch

from sqlalchemy import schema

from app.core.init_db import init_db


def test_init_db_creates_schema_and_missing_tables():
    engine = MagicMock()
    connection = engine.begin.return_value.__enter__.return_value

    with patch("app.core.init_db.Base.metadata.create_all") as create_all:
        init_db(engine)

    statement = connection.execute.call_args.args[0]
    assert isinstance(statement, schema.CreateSchema)
    assert statement.element == "website"
    assert statement.if_not_exists is True
    create_all.assert_called_once_with(engine)
