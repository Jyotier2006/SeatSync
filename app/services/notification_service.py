import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, subject: str, body: str) -> None:
        raise NotImplementedError


class LoggingNotificationChannel(NotificationChannel):
    """Development adapter. Replace with SendGrid, SES, Twilio, etc."""

    def send(self, recipient: str, subject: str, body: str) -> None:
        logger.info(
            "notification recipient=%s subject=%s body=%s",
            recipient,
            subject,
            body,
        )


class NotificationService:
    def __init__(self, channel: NotificationChannel | None = None):
        self.channel = channel or LoggingNotificationChannel()

    def send_booking_confirmation(self, recipient: str, booking_reference: str) -> None:
        self.channel.send(
            recipient=recipient,
            subject=f"SeatSync booking {booking_reference} confirmed",
            body=(
                f"Your booking {booking_reference} is confirmed. "
                "Open SeatSync to view the latest booking details."
            ),
        )

    def send_payment_failure(self, recipient: str, booking_reference: str) -> None:
        self.channel.send(
            recipient=recipient,
            subject=f"Payment failed for {booking_reference}",
            body="The payment did not complete and the reserved seats were released.",
        )
