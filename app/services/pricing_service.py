from decimal import ROUND_HALF_UP, Decimal

from app.models.enums import SeatCategory


class PricingService:
    """Strategy-like pricing component kept independent from persistence."""

    MULTIPLIERS = {
        SeatCategory.STANDARD: Decimal("1.00"),
        SeatCategory.PREMIUM: Decimal("1.35"),
        SeatCategory.RECLINER: Decimal("1.75"),
    }

    def calculate(self, base_price: Decimal, category: SeatCategory) -> Decimal:
        return (base_price * self.MULTIPLIERS[category]).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
