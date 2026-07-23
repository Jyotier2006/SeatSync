from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.catalog import Movie, Screen, Show, ShowSeat


class CatalogRepository:
    def list_movies(self, db: Session, city: str | None = None) -> list[Movie]:
        query = select(Movie).order_by(Movie.title)
        if city:
            query = (
                query.join(Movie.shows)
                .join(Show.screen)
                .join(Screen.venue)
            )
        return list(db.scalars(query).unique())

    def get_show_with_seats(self, db: Session, show_id: str) -> Show | None:
        return db.scalar(
            select(Show)
            .where(Show.id == show_id)
            .options(joinedload(Show.show_seats).joinedload(ShowSeat.seat))
        )
