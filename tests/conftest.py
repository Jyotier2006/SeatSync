from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.catalog import Movie, Screen, Seat, Show, ShowSeat, Venue
from app.models.enums import SeatCategory, UserRole
from app.models.user import User


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    yield TestingSession
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db(session_factory):
    with session_factory() as session:
        yield session


@pytest.fixture()
def client(session_factory):
    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(db):
    customer = User(
        email="customer@example.com",
        full_name="Customer",
        password_hash=hash_password("Password123"),
    )
    other = User(
        email="other@example.com",
        full_name="Other",
        password_hash=hash_password("Password123"),
    )
    admin = User(
        email="admin@example.com",
        full_name="Admin",
        password_hash=hash_password("Password123"),
        role=UserRole.ADMIN,
    )
    movie = Movie(
        title="Test Movie",
        duration_minutes=120,
        language="English",
        description="",
    )
    venue = Venue(name="Test Venue", city="Ahmedabad", address="Test Road")
    screen = Screen(name="Screen 1", venue=venue)
    db.add_all([customer, other, admin, movie, venue])
    db.flush()
    seat1 = Seat(screen_id=screen.id, row_label="A", number=1, category=SeatCategory.STANDARD)
    seat2 = Seat(screen_id=screen.id, row_label="A", number=2, category=SeatCategory.PREMIUM)
    db.add_all([seat1, seat2])
    db.flush()
    starts = datetime.now(UTC) + timedelta(days=1)
    show = Show(
        movie_id=movie.id,
        screen_id=screen.id,
        starts_at=starts,
        ends_at=starts + timedelta(minutes=140),
    )
    db.add(show)
    db.flush()
    show_seat1 = ShowSeat(show_id=show.id, seat_id=seat1.id, price=Decimal("200.00"))
    show_seat2 = ShowSeat(show_id=show.id, seat_id=seat2.id, price=Decimal("300.00"))
    db.add_all([show_seat1, show_seat2])
    db.commit()
    return {
        "customer": customer,
        "other": other,
        "admin": admin,
        "movie": movie,
        "venue": venue,
        "screen": screen,
        "show": show,
        "show_seats": [show_seat1, show_seat2],
    }


def login(client: TestClient, email: str, password: str = "Password123") -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
