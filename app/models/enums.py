from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class SeatCategory(StrEnum):
    STANDARD = "STANDARD"
    PREMIUM = "PREMIUM"
    RECLINER = "RECLINER"


class ShowSeatStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    LOCKED = "LOCKED"
    BOOKED = "BOOKED"


class BookingStatus(StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(StrEnum):
    UPI = "UPI"
    CARD = "CARD"
    WALLET = "WALLET"


class OutboxStatus(StrEnum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
