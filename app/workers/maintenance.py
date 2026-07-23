"""Maintenance commands suitable for cron, Celery Beat, or a Kubernetes CronJob."""

from app.db.session import SessionLocal
from app.services.seat_lock_service import SeatLockService


def release_expired_seat_locks() -> int:
    with SessionLocal() as db:
        count = SeatLockService().release_expired(db)
        db.commit()
        return count


if __name__ == "__main__":
    print(f"Released {release_expired_seat_locks()} expired seat lock(s)")
