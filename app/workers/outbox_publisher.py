"""Small transactional-outbox publisher.

Production deployments should run this continuously through a process manager,
Celery worker, or Kubernetes deployment. The development implementation sends
notifications through a logging adapter and safely retries failed events.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import SessionLocal
from app.models.booking import Booking
from app.models.enums import OutboxStatus
from app.models.outbox import OutboxEvent
from app.services.notification_service import NotificationService


class OutboxPublisher:
    def __init__(self, notifications: NotificationService | None = None):
        self.notifications = notifications or NotificationService()

    def publish_batch(self, limit: int = 100) -> int:
        published = 0
        with SessionLocal() as db:
            events = list(
                db.scalars(
                    select(OutboxEvent)
                    .where(OutboxEvent.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]))
                    .order_by(OutboxEvent.created_at)
                    .limit(limit)
                )
            )
            for event in events:
                try:
                    booking = db.scalar(
                        select(Booking)
                        .where(Booking.id == event.aggregate_id)
                        .options(joinedload(Booking.user))
                    )
                    if booking is None:
                        raise RuntimeError("Booking referenced by outbox event does not exist")
                    if event.event_type == "BookingConfirmed":
                        self.notifications.send_booking_confirmation(
                            booking.user.email, booking.booking_reference
                        )
                    elif event.event_type == "BookingPaymentFailed":
                        self.notifications.send_payment_failure(
                            booking.user.email, booking.booking_reference
                        )
                    event.status = OutboxStatus.PUBLISHED
                    event.published_at = datetime.now(UTC)
                    published += 1
                except Exception:
                    event.status = OutboxStatus.FAILED
                    event.attempts += 1
            db.commit()
        return published


if __name__ == "__main__":
    print(f"Published {OutboxPublisher().publish_batch()} event(s)")
