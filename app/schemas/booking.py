from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BookingStatus


class SeatLockRequest(BaseModel):
    show_id: str
    show_seat_ids: list[str] = Field(min_length=1, max_length=10)


class SeatLockResponse(BaseModel):
    lock_token: str
    show_id: str
    show_seat_ids: list[str]
    expires_at: datetime


class BookingCreate(BaseModel):
    lock_token: str


class BookingSeatResponse(BaseModel):
    show_seat_id: str
    row_label: str
    number: int
    price: Decimal


class BookingResponse(BaseModel):
    id: str
    booking_reference: str
    show_id: str
    status: BookingStatus
    total_amount: Decimal
    expires_at: datetime
    created_at: datetime
    seats: list[BookingSeatResponse]

    model_config = ConfigDict(from_attributes=True)
