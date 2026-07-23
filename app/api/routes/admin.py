from datetime import timedelta
from decimal import Decimal

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.models.catalog import Movie, Screen, Seat, Show, ShowSeat, Venue
from app.models.enums import SeatCategory
from app.schemas.catalog import (
    MovieCreate,
    MovieResponse,
    ScreenCreate,
    ScreenResponse,
    SeatBulkCreate,
    SeatResponse,
    ShowCreate,
    ShowResponse,
    VenueCreate,
    VenueResponse,
)
from app.services.errors import ConflictError, NotFoundError
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/admin", tags=["administration"])
pricing = PricingService()


@router.post("/movies", response_model=MovieResponse, status_code=201)
def create_movie(payload: MovieCreate, db: DbSession, _: AdminUser) -> Movie:
    movie = Movie(**payload.model_dump())
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


@router.post("/venues", response_model=VenueResponse, status_code=201)
def create_venue(payload: VenueCreate, db: DbSession, _: AdminUser) -> Venue:
    venue = Venue(**payload.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


@router.post("/screens", response_model=ScreenResponse, status_code=201)
def create_screen(payload: ScreenCreate, db: DbSession, _: AdminUser) -> Screen:
    if not db.get(Venue, payload.venue_id):
        raise NotFoundError("Venue not found")
    screen = Screen(**payload.model_dump())
    db.add(screen)
    db.commit()
    db.refresh(screen)
    return screen


@router.post("/screens/{screen_id}/seats", response_model=list[SeatResponse], status_code=201)
def create_seats(
    screen_id: str, payload: SeatBulkCreate, db: DbSession, _: AdminUser
) -> list[Seat]:
    if not db.get(Screen, screen_id):
        raise NotFoundError("Screen not found")
    if db.scalar(select(Seat).where(Seat.screen_id == screen_id).limit(1)):
        raise ConflictError("Seats already exist for this screen")
    seats = [
        Seat(
            screen_id=screen_id,
            row_label=row.upper(),
            number=number,
            category=payload.category,
        )
        for row in payload.rows
        for number in range(1, payload.seats_per_row + 1)
    ]
    db.add_all(seats)
    db.commit()
    return seats


@router.post("/shows", response_model=ShowResponse, status_code=201)
def create_show(payload: ShowCreate, db: DbSession, _: AdminUser) -> Show:
    movie = db.get(Movie, payload.movie_id)
    screen = db.get(Screen, payload.screen_id)
    if not movie:
        raise NotFoundError("Movie not found")
    if not screen:
        raise NotFoundError("Screen not found")
    if payload.starts_at.tzinfo is None:
        raise ConflictError("starts_at must include a timezone")

    ends_at = payload.starts_at + timedelta(minutes=movie.duration_minutes + 20)
    overlap = db.scalar(
        select(Show).where(
            Show.screen_id == payload.screen_id,
            Show.starts_at < ends_at,
            Show.ends_at > payload.starts_at,
        )
    )
    if overlap:
        raise ConflictError("This show overlaps another show on the same screen")

    show = Show(
        movie_id=payload.movie_id,
        screen_id=payload.screen_id,
        starts_at=payload.starts_at,
        ends_at=ends_at,
    )
    db.add(show)
    db.flush()
    seats = list(db.scalars(select(Seat).where(Seat.screen_id == payload.screen_id)))
    if not seats:
        raise ConflictError("Create screen seats before creating a show")
    for seat in seats:
        multiplier = {
            SeatCategory.STANDARD: Decimal("1.00"),
            SeatCategory.PREMIUM: payload.premium_multiplier,
            SeatCategory.RECLINER: payload.recliner_multiplier,
        }[seat.category]
        db.add(
            ShowSeat(
                show_id=show.id,
                seat_id=seat.id,
                price=(payload.base_price * multiplier).quantize(Decimal("0.01")),
            )
        )
    db.commit()
    db.refresh(show)
    return show
