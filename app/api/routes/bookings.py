from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.booking import (
    BookingCreate,
    BookingResponse,
    BookingSeatResponse,
    SeatLockRequest,
    SeatLockResponse,
)
from app.schemas.common import MessageResponse
from app.services.booking_service import BookingService
from app.services.seat_lock_service import SeatLockService

router = APIRouter(tags=["bookings"])
seat_locks = SeatLockService()
bookings = BookingService(seat_locks)


def serialize_booking(booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        booking_reference=booking.booking_reference,
        show_id=booking.show_id,
        status=booking.status,
        total_amount=booking.total_amount,
        expires_at=booking.expires_at,
        created_at=booking.created_at,
        seats=[
            BookingSeatResponse(
                show_seat_id=item.show_seat_id,
                row_label=item.show_seat.seat.row_label,
                number=item.show_seat.seat.number,
                price=item.price,
            )
            for item in booking.seats
        ],
    )


@router.post("/seat-locks", response_model=SeatLockResponse, status_code=201)
def lock_seats(
    payload: SeatLockRequest, db: DbSession, current_user: CurrentUser
) -> SeatLockResponse:
    token, expiry = seat_locks.lock_seats(
        db, current_user.id, payload.show_id, payload.show_seat_ids
    )
    return SeatLockResponse(
        lock_token=token,
        show_id=payload.show_id,
        show_seat_ids=payload.show_seat_ids,
        expires_at=expiry,
    )


@router.delete("/seat-locks/{lock_token}", response_model=MessageResponse)
def release_lock(
    lock_token: str, db: DbSession, current_user: CurrentUser
) -> MessageResponse:
    # The token is high entropy; user ownership is still verified by the lock rows.
    from sqlalchemy import select
    from app.models.booking import SeatLock
    from app.services.errors import NotFoundError

    owned = db.scalar(
        select(SeatLock).where(
            SeatLock.lock_token == lock_token,
            SeatLock.user_id == current_user.id,
            SeatLock.released_at.is_(None),
        )
    )
    if not owned:
        raise NotFoundError("Active lock not found")
    count = seat_locks.release_token(db, lock_token)
    db.commit()
    return MessageResponse(message=f"Released {count} seat(s)")


@router.post("/bookings", response_model=BookingResponse, status_code=201)
def create_booking(
    payload: BookingCreate, db: DbSession, current_user: CurrentUser
) -> BookingResponse:
    booking = bookings.create_booking(db, current_user.id, payload.lock_token)
    return serialize_booking(booking)


@router.get("/bookings", response_model=list[BookingResponse])
def list_bookings(db: DbSession, current_user: CurrentUser) -> list[BookingResponse]:
    return [serialize_booking(item) for item in bookings.list_user_bookings(db, current_user.id)]


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: str, db: DbSession, current_user: CurrentUser
) -> BookingResponse:
    return serialize_booking(bookings.get_booking(db, booking_id, current_user.id))


@router.post("/bookings/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: str, db: DbSession, current_user: CurrentUser
) -> BookingResponse:
    return serialize_booking(bookings.cancel(db, booking_id, current_user.id))
