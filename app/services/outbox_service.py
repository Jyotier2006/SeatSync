from sqlalchemy.orm import Session

from app.models.outbox import OutboxEvent


class OutboxService:
    def add(self, db: Session, aggregate_type: str, aggregate_id: str, event_type: str, payload: dict) -> None:
        db.add(
            OutboxEvent(
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_type=event_type,
                payload=payload,
            )
        )
