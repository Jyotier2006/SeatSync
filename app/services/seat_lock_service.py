import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.booking import SeatLock
from app.models.catalog import ShowSeat
from app.models.enums import ShowSeatStatus
from app.services.errors import ConflictError, NotFoundError


class SeatLockService:
    def release_expired(self, db: Session, show_id: str | None = None) -> int:
        now = datetime.now(UTC)
        query = select(ShowSeat).where(
            ShowSeat.status == ShowSeatStatus.LOCKED,
            ShowSeat.lock_expires_at.is_not(None),
            ShowSeat.lock_expires_at <= now,
        )
        if show_id:
            query = query.where(ShowSeat.show_id == show_id)
        expired = list(db.scalars(query))
        if not expired:
            return 0

        tokens = {seat.lock_token for seat in expired if seat.lock_token}
        for seat in expired:
            seat.status = ShowSeatStatus.AVAILABLE
            seat.lock_token = None
            seat.locked_by = None
            seat.lock_expires_at = None
            seat.version += 1

        if tokens:
            locks = list(
                db.scalars(
                    select(SeatLock).where(
                        SeatLock.lock_token.in_(tokens), SeatLock.released_at.is_(None)
                    )
                )
            )
            for lock in locks:
                lock.released_at = now
        db.flush()
        return len(expired)

    def lock_seats(
        self, db: Session, user_id: str, show_id: str, show_seat_ids: list[str]
    ) -> tuple[str, datetime]:
        unique_ids = list(dict.fromkeys(show_seat_ids))
        if len(unique_ids) != len(show_seat_ids):
            raise ConflictError("Duplicate seat IDs are not allowed")

        self.release_expired(db, show_id)
        seats = list(
            db.scalars(
                select(ShowSeat).where(
                    ShowSeat.show_id == show_id, ShowSeat.id.in_(unique_ids)
                )
            )
        )
        if len(seats) != len(unique_ids):
            raise NotFoundError("One or more seats do not belong to this show")

        lock_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(
            seconds=get_settings().seat_lock_ttl_seconds
        )

        result = db.execute(
            update(ShowSeat)
            .where(
                and_(
                    ShowSeat.show_id == show_id,
                    ShowSeat.id.in_(unique_ids),
                    ShowSeat.status == ShowSeatStatus.AVAILABLE,
                )
            )
            .values(
                status=ShowSeatStatus.LOCKED,
                lock_token=lock_token,
                locked_by=user_id,
                lock_expires_at=expires_at,
                version=ShowSeat.version + 1,
            )
        )
        if result.rowcount != len(unique_ids):
            db.rollback()
            raise ConflictError("One or more selected seats are no longer available")

        for seat_id in unique_ids:
            db.add(
                SeatLock(
                    lock_token=lock_token,
                    show_seat_id=seat_id,
                    user_id=user_id,
                    expires_at=expires_at,
                )
            )
        db.commit()
        return lock_token, expires_at

    def release_token(self, db: Session, lock_token: str) -> int:
        now = datetime.now(UTC)
        seats = list(
            db.scalars(
                select(ShowSeat).where(
                    ShowSeat.lock_token == lock_token,
                    ShowSeat.status == ShowSeatStatus.LOCKED,
                )
            )
        )
        for seat in seats:
            seat.status = ShowSeatStatus.AVAILABLE
            seat.lock_token = None
            seat.locked_by = None
            seat.lock_expires_at = None
            seat.version += 1
        locks = list(
            db.scalars(
                select(SeatLock).where(
                    SeatLock.lock_token == lock_token,
                    SeatLock.released_at.is_(None),
                )
            )
        )
        for lock in locks:
            lock.released_at = now
        db.flush()
        return len(seats)
