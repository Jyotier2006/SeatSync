from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession
from app.models.catalog import Movie, Screen, Show, ShowSeat
from app.schemas.catalog import MovieResponse, MovieShowResponse, ShowSeatResponse
from app.services.errors import NotFoundError
from app.services.seat_lock_service import SeatLockService

router = APIRouter(tags=["catalog"])
seat_locks = SeatLockService()


@router.get("/movies", response_model=list[MovieResponse])
def list_movies(db: DbSession, language: str | None = None) -> list[Movie]:
    query = select(Movie).order_by(Movie.title)
    if language:
        query = query.where(Movie.language == language)
    return list(db.scalars(query))


@router.get("/movies/{movie_id}", response_model=MovieResponse)
def get_movie(movie_id: str, db: DbSession) -> Movie:
    movie = db.get(Movie, movie_id)
    if not movie:
        raise NotFoundError("Movie not found")
    return movie


@router.get("/movies/{movie_id}/shows", response_model=list[MovieShowResponse])
def movie_shows(
    movie_id: str,
    db: DbSession,
    city: str | None = Query(default=None),
) -> list[MovieShowResponse]:
    query = (
        select(Show)
        .where(Show.movie_id == movie_id)
        .options(joinedload(Show.screen).joinedload(Screen.venue))
        .order_by(Show.starts_at)
    )
    shows = list(db.scalars(query))
    result = []
    for show in shows:
        venue = show.screen.venue
        if city and venue.city.lower() != city.lower():
            continue
        result.append(
            MovieShowResponse(
                show_id=show.id,
                starts_at=show.starts_at,
                ends_at=show.ends_at,
                venue_name=venue.name,
                city=venue.city,
                screen_name=show.screen.name,
            )
        )
    return result


@router.get("/shows/{show_id}/seats", response_model=list[ShowSeatResponse])
def show_seats(show_id: str, db: DbSession) -> list[ShowSeatResponse]:
    show = db.get(Show, show_id)
    if not show:
        raise NotFoundError("Show not found")
    seat_locks.release_expired(db, show_id)
    db.commit()
    seats = list(
        db.scalars(
            select(ShowSeat)
            .where(ShowSeat.show_id == show_id)
            .options(joinedload(ShowSeat.seat))
            .order_by(ShowSeat.seat_id)
        )
    )
    return [
        ShowSeatResponse(
            id=item.id,
            show_id=item.show_id,
            seat_id=item.seat_id,
            row_label=item.seat.row_label,
            number=item.seat.number,
            category=item.seat.category,
            price=item.price,
            status=item.status,
        )
        for item in sorted(seats, key=lambda x: (x.seat.row_label, x.seat.number))
    ]
