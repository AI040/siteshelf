"""ORM model for the `websites` table."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import WEBSITE_TYPES
from app.core.database import Base

# UTC "now" without a time zone, matching the TIMESTAMP WITHOUT TIME ZONE columns
UTC_NOW = text("timezone('utc', now())")


class Website(Base):
    __tablename__ = "website_info"

    website_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    website_name: Mapped[str] = mapped_column(String(255), nullable=False)
    website_link: Mapped[str] = mapped_column(String(2048), nullable=False)
    website_type: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=UTC_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=False, server_default=UTC_NOW
    )

    __table_args__ = (
        Index("idx_websites_website_name", "website_name"),
        Index("idx_websites_website_type", "website_type"),
        CheckConstraint(
            "website_type IN (" + ", ".join(f"'{t}'" for t in WEBSITE_TYPES) + ")",
            name="ck_websites_website_type",
        ),
        {"schema": "website"},
    )

    def __repr__(self) -> str:
        return f"<Website {self.website_id} {self.website_name!r}>"
