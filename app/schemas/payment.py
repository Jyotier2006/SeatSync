from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    booking_id: str
    method: PaymentMethod
    idempotency_key: str = Field(min_length=8, max_length=100)


class PaymentResultRequest(BaseModel):
    success: bool
    gateway_reference: str | None = None
    failure_reason: str | None = None


class PaymentResponse(BaseModel):
    id: str
    booking_id: str
    idempotency_key: str
    gateway_reference: str | None
    method: PaymentMethod
    status: PaymentStatus
    amount: Decimal
    failure_reason: str | None

    model_config = ConfigDict(from_attributes=True)
