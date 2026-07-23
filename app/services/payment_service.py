import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import as_utc
from app.models.booking import Booking
from app.models.catalog import ShowSeat
from app.models.enums import BookingStatus, PaymentMethod, PaymentStatus, ShowSeatStatus
from app.models.payment import Payment
from app.services.errors import ConflictError, NotFoundError
from app.services.outbox_service import OutboxService
from app.services.seat_lock_service import SeatLockService


class PaymentService:
    def __init__(
        self,
        seat_locks: SeatLockService | None = None,
        outbox: OutboxService | None = None,
    ):
        self.seat_locks = seat_locks or SeatLockService()
        self.outbox = outbox or OutboxService()

    def initiate(
        self,
        db: Session,
        user_id: str,
        booking_id: str,
        method: PaymentMethod,
        idempotency_key: str,
    ) -> Payment:
        existing = db.scalar(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
        if existing:
            if existing.booking_id != booking_id:
                raise ConflictError("Idempotency key is already used for another booking")
            return existing

        booking = db.scalar(
            select(Booking).where(Booking.id == booking_id, Booking.user_id == user_id)
        )
        if not booking:
            raise NotFoundError("Booking not found")
        if booking.status != BookingStatus.PENDING_PAYMENT:
            raise ConflictError("Booking is not awaiting payment")
        if as_utc(booking.expires_at) <= datetime.now(UTC):
            self.seat_locks.release_token(db, booking.lock_token)
            booking.status = BookingStatus.EXPIRED
            db.commit()
            raise ConflictError("Booking has expired")

        payment = Payment(
            booking_id=booking.id,
            idempotency_key=idempotency_key,
            method=method,
            status=PaymentStatus.PENDING,
            amount=booking.total_amount,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def apply_mock_result(
        self,
        db: Session,
        user_id: str,
        payment_id: str,
        success: bool,
        gateway_reference: str | None,
        failure_reason: str | None,
    ) -> Payment:
        payment = db.scalar(
            select(Payment).join(Booking).where(
                Payment.id == payment_id, Booking.user_id == user_id
            )
        )
        if not payment:
            raise NotFoundError("Payment not found")
        if payment.status in {PaymentStatus.SUCCESS, PaymentStatus.FAILED}:
            return payment

        booking = db.get(Booking, payment.booking_id)
        assert booking is not None
        now = datetime.now(UTC)

        is_still_pending = booking.status == BookingStatus.PENDING_PAYMENT
        if success and as_utc(booking.expires_at) > now and is_still_pending:
            payment.status = PaymentStatus.SUCCESS
            payment.gateway_reference = gateway_reference or f"MOCK-{secrets.token_hex(6)}"
            booking.status = BookingStatus.CONFIRMED
            seats = list(
                db.scalars(
                    select(ShowSeat).where(
                        ShowSeat.lock_token == booking.lock_token,
                        ShowSeat.locked_by == user_id,
                        ShowSeat.status == ShowSeatStatus.LOCKED,
                    )
                )
            )
            if len(seats) != len(booking.seats):
                db.rollback()
                raise ConflictError("Locked seats are no longer available")
            for seat in seats:
                seat.status = ShowSeatStatus.BOOKED
                seat.lock_expires_at = None
                seat.version += 1
            self.outbox.add(
                db,
                aggregate_type="Booking",
                aggregate_id=booking.id,
                event_type="BookingConfirmed",
                payload={
                    "booking_id": booking.id,
                    "booking_reference": booking.booking_reference,
                    "user_id": user_id,
                },
            )
        else:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = failure_reason or (
                "Booking expired before payment confirmation" if success else "Payment declined"
            )
            booking.status = (
                BookingStatus.EXPIRED
                if as_utc(booking.expires_at) <= now
                else BookingStatus.PAYMENT_FAILED
            )
            self.seat_locks.release_token(db, booking.lock_token)
            self.outbox.add(
                db,
                aggregate_type="Booking",
                aggregate_id=booking.id,
                event_type="BookingPaymentFailed",
                payload={"booking_id": booking.id, "reason": payment.failure_reason},
            )

        db.commit()
        db.refresh(payment)
        return payment
