from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.payment import PaymentCreate, PaymentResponse, PaymentResultRequest
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])
service = PaymentService()


@router.post("", response_model=PaymentResponse, status_code=201)
def initiate_payment(
    payload: PaymentCreate, db: DbSession, current_user: CurrentUser
):
    return service.initiate(
        db,
        current_user.id,
        payload.booking_id,
        payload.method,
        payload.idempotency_key,
    )


@router.post("/{payment_id}/mock-result", response_model=PaymentResponse)
def mock_payment_result(
    payment_id: str,
    payload: PaymentResultRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    return service.apply_mock_result(
        db,
        current_user.id,
        payment_id,
        payload.success,
        payload.gateway_reference,
        payload.failure_reason,
    )
