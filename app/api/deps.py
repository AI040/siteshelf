"""Shared FastAPI dependencies."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_session_factory


def get_db_session() -> Iterator[Session]:
    # The service layer commits / rolls back; this only guarantees the close.
    with get_session_factory()() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db_session)]
