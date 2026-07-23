import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import OutboxStatus


class OutboxEvent(Base):
    __tablename__ = "outbox_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    aggregate_type: Mapped[str] = mapped_column(String(100), index=True)
    aggregate_id: Mapped[str] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(150), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[OutboxStatus] = mapped_column(default=OutboxStatus.PENDING, index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
