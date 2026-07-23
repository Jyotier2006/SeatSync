import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.time import as_utc
from app.models.booking import Booking, BookingSeat, SeatLock
from app.models.catalog import ShowSeat
from app.models.enums import BookingStatus, ShowSeatStatus
from app.services.errors import ConflictError, NotFoundError
from app.services.seat_lock_service import SeatLockService


class BookingService:
    def __init__(self, seat_locks: SeatLockService | None = None):
        self.seat_locks = seat_locks or SeatLockService()

    @staticmethod
    def _reference() -> str:
        return f"SS{secrets.token_hex(4).upper()}"

    def create_booking(self, db: Session, user_id: str, lock_token: str) -> Booking:
        self.seat_locks.release_expired(db)
        now = datetime.now(UTC)
        locks = list(
            db.scalars(
                select(SeatLock).where(
                    SeatLock.lock_token == lock_token,
                    SeatLock.user_id == user_id,
                    SeatLock.released_at.is_(None),
                    SeatLock.expires_at > now,
                )
            )
        )
        if not locks:
            raise ConflictError("Seat lock is missing or has expired")

        seat_ids = [lock.show_seat_id for lock in locks]
        seats = list(
            db.scalars(
                select(ShowSeat).where(
                    ShowSeat.id.in_(seat_ids),
                    ShowSeat.status == ShowSeatStatus.LOCKED,
                    ShowSeat.lock_token == lock_token,
                    ShowSeat.locked_by == user_id,
                )
            )
        )
        if len(seats) != len(seat_ids):
            raise ConflictError("Seat lock is inconsistent; select the seats again")
        show_ids = {seat.show_id for seat in seats}
        if len(show_ids) != 1:
            raise ConflictError("All locked seats must belong to the same show")

        existing = db.scalar(
            select(Booking).where(
                Booking.lock_token == lock_token,
                Booking.user_id == user_id,
                Booking.status == BookingStatus.PENDING_PAYMENT,
            )
        )
        if existing:
            return self.get_booking(db, existing.id, user_id)

        total = sum((Decimal(seat.price) for seat in seats), start=Decimal("0.00"))
        expiry = min(
            min(as_utc(lock.expires_at) for lock in locks),
            now + timedelta(seconds=get_settings().booking_payment_ttl_seconds),
        )
        booking = Booking(
            booking_reference=self._reference(),
            user_id=user_id,
            show_id=next(iter(show_ids)),
            lock_token=lock_token,
            total_amount=total,
            expires_at=expiry,
            status=BookingStatus.PENDING_PAYMENT,
        )
        db.add(booking)
        db.flush()
        for seat in seats:
            db.add(
                BookingSeat(
                    booking_id=booking.id,
                    show_seat_id=seat.id,
                    price=seat.price,
                )
            )
        db.commit()
        return self.get_booking(db, booking.id, user_id)

    def get_booking(self, db: Session, booking_id: str, user_id: str | None = None) -> Booking:
        query = (
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                joinedload(Booking.seats)
                .joinedload(BookingSeat.show_seat)
                .joinedload(ShowSeat.seat)
            )
        )
        if user_id:
            query = query.where(Booking.user_id == user_id)
        booking = db.scalar(query)
        if not booking:
            raise NotFoundError("Booking not found")
        return booking

    def list_user_bookings(self, db: Session, user_id: str) -> list[Booking]:
        return list(
            db.scalars(
                select(Booking)
                .where(Booking.user_id == user_id)
                .order_by(Booking.created_at.desc())
                .options(
                    joinedload(Booking.seats)
                    .joinedload(BookingSeat.show_seat)
                    .joinedload(ShowSeat.seat)
                )
            ).unique()
        )

    def cancel(self, db: Session, booking_id: str, user_id: str) -> Booking:
        booking = self.get_booking(db, booking_id, user_id)
        if booking.status not in {
            BookingStatus.CONFIRMED,
            BookingStatus.PENDING_PAYMENT,
        }:
            raise ConflictError(f"Booking cannot be cancelled from {booking.status}")

        if booking.status == BookingStatus.PENDING_PAYMENT:
            self.seat_locks.release_token(db, booking.lock_token)
            booking.status = BookingStatus.CANCELLED
        else:
            for item in booking.seats:
                show_seat = item.show_seat
                show_seat.status = ShowSeatStatus.AVAILABLE
                show_seat.lock_token = None
                show_seat.locked_by = None
                show_seat.lock_expires_at = None
                show_seat.version += 1
            booking.status = BookingStatus.REFUNDED
        db.commit()
        return self.get_booking(db, booking.id, user_id)
