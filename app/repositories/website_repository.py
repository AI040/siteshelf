"""Database access for websites. No business rules here, only SQL."""

from sqlalchemy import func, literal_column
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.website import Website


def upsert_many(session: Session, rows: list[dict], batch_size: int = 5000) -> tuple[int, int]:
    """Insert new websites; for ones that already exist, refresh updated_at only.

    Returns (inserted, existing). Does not commit: the caller owns the transaction.
    """
    inserted = existing = 0

    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        stmt = (
            pg_insert(Website)
            .values(batch)
            .on_conflict_do_update(
                index_elements=[Website.website_id],
                set_={"updated_at": func.timezone("utc", func.now())},
            )
            # xmax = 0 -> row was freshly inserted; otherwise it already existed
            .returning(literal_column("(xmax = 0)"))
        )
        flags = session.execute(stmt).scalars().all()
        new = sum(1 for flag in flags if flag)
        inserted += new
        existing += len(flags) - new

    return inserted, existing
