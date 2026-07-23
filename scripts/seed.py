from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.catalog import Movie, Screen, Seat, Show, ShowSeat, Venue
from app.models.enums import SeatCategory, UserRole
from app.models.user import User
from app.services.pricing_service import PricingService

Base.metadata.create_all(bind=engine)
pricing = PricingService()

with SessionLocal() as db:
    admin = db.scalar(select(User).where(User.email == "admin@seatsync.dev"))
    if not admin:
        admin = User(
            email="admin@seatsync.dev",
            full_name="SeatSync Admin",
            password_hash=hash_password("Admin@12345"),
            role=UserRole.ADMIN,
        )
        db.add(admin)

    customer = db.scalar(select(User).where(User.email == "demo@seatsync.dev"))
    if not customer:
        customer = User(
            email="demo@seatsync.dev",
            full_name="Demo Customer",
            password_hash=hash_password("Demo@12345"),
        )
        db.add(customer)

    if not db.scalar(select(Movie).limit(1)):
        movie = Movie(
            title="Concurrency: The Movie",
            description="A demo movie used to explore race conditions.",
            duration_minutes=135,
            language="English",
            certificate="U/A",
        )
        venue = Venue(
            name="SeatSync Cinema",
            city="Ahmedabad",
            address="SG Highway, Ahmedabad, Gujarat",
        )
        screen = Screen(name="Screen 1", venue=venue)
        db.add_all([movie, venue])
        db.flush()

        for row in ["A", "B", "C", "D"]:
            category = SeatCategory.PREMIUM if row in {"C", "D"} else SeatCategory.STANDARD
            for number in range(1, 9):
                db.add(Seat(screen_id=screen.id, row_label=row, number=number, category=category))
        db.flush()

        starts_at = datetime.now(UTC) + timedelta(days=1)
        show = Show(
            movie_id=movie.id,
            screen_id=screen.id,
            starts_at=starts_at,
            ends_at=starts_at + timedelta(minutes=155),
        )
        db.add(show)
        db.flush()
        seats = list(db.scalars(select(Seat).where(Seat.screen_id == screen.id)))
        for seat in seats:
            db.add(
                ShowSeat(
                    show_id=show.id,
                    seat_id=seat.id,
                    price=pricing.calculate(Decimal("250.00"), seat.category),
                )
            )

    db.commit()

print("Seed complete")
print("Admin: admin@seatsync.dev / Admin@12345")
print("Customer: demo@seatsync.dev / Demo@12345")
