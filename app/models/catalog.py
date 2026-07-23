import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SeatCategory, ShowSeatStatus


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(String(2000), default="")
    duration_minutes: Mapped[int]
    language: Mapped[str] = mapped_column(String(80))
    certificate: Mapped[str] = mapped_column(String(20), default="U/A")
    poster_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    shows = relationship("Show", back_populates="movie")


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(100), index=True)
    address: Mapped[str] = mapped_column(String(500))

    screens = relationship("Screen", back_populates="venue", cascade="all, delete-orphan")


class Screen(Base):
    __tablename__ = "screens"
    __table_args__ = (UniqueConstraint("venue_id", "name", name="uq_screen_venue_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    venue_id: Mapped[str] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))

    venue = relationship("Venue", back_populates="screens")
    seats = relationship("Seat", back_populates="screen", cascade="all, delete-orphan")
    shows = relationship("Show", back_populates="screen")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (
        UniqueConstraint("screen_id", "row_label", "number", name="uq_seat_screen_position"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    screen_id: Mapped[str] = mapped_column(ForeignKey("screens.id", ondelete="CASCADE"), index=True)
    row_label: Mapped[str] = mapped_column(String(10))
    number: Mapped[int]
    category: Mapped[SeatCategory] = mapped_column(default=SeatCategory.STANDARD)

    screen = relationship("Screen", back_populates="seats")
    show_seats = relationship("ShowSeat", back_populates="seat")


class Show(Base):
    __tablename__ = "shows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    movie_id: Mapped[str] = mapped_column(ForeignKey("movies.id"), index=True)
    screen_id: Mapped[str] = mapped_column(ForeignKey("screens.id"), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    movie = relationship("Movie", back_populates="shows")
    screen = relationship("Screen", back_populates="shows")
    show_seats = relationship("ShowSeat", back_populates="show", cascade="all, delete-orphan")


class ShowSeat(Base):
    __tablename__ = "show_seats"
    __table_args__ = (UniqueConstraint("show_id", "seat_id", name="uq_show_seat"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    show_id: Mapped[str] = mapped_column(ForeignKey("shows.id", ondelete="CASCADE"), index=True)
    seat_id: Mapped[str] = mapped_column(ForeignKey("seats.id"), index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[ShowSeatStatus] = mapped_column(default=ShowSeatStatus.AVAILABLE, index=True)
    lock_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    locked_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    lock_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    version: Mapped[int] = mapped_column(default=0)

    show = relationship("Show", back_populates="show_seats")
    seat = relationship("Seat", back_populates="show_seats")
