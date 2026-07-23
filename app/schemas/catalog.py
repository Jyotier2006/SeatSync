from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SeatCategory, ShowSeatStatus


class MovieCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    duration_minutes: int = Field(gt=0, le=600)
    language: str
    certificate: str = "U/A"
    poster_url: str | None = None


class MovieResponse(MovieCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class VenueCreate(BaseModel):
    name: str
    city: str
    address: str


class VenueResponse(VenueCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class ScreenCreate(BaseModel):
    venue_id: str
    name: str


class ScreenResponse(ScreenCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)


class SeatBulkCreate(BaseModel):
    rows: list[str] = Field(min_length=1)
    seats_per_row: int = Field(gt=0, le=100)
    category: SeatCategory = SeatCategory.STANDARD


class SeatResponse(BaseModel):
    id: str
    screen_id: str
    row_label: str
    number: int
    category: SeatCategory
    model_config = ConfigDict(from_attributes=True)


class ShowCreate(BaseModel):
    movie_id: str
    screen_id: str
    starts_at: datetime
    base_price: Decimal = Field(gt=0)
    premium_multiplier: Decimal = Decimal("1.35")
    recliner_multiplier: Decimal = Decimal("1.75")


class ShowResponse(BaseModel):
    id: str
    movie_id: str
    screen_id: str
    starts_at: datetime
    ends_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ShowSeatResponse(BaseModel):
    id: str
    show_id: str
    seat_id: str
    row_label: str
    number: int
    category: SeatCategory
    price: Decimal
    status: ShowSeatStatus


class MovieShowResponse(BaseModel):
    show_id: str
    starts_at: datetime
    ends_at: datetime
    venue_name: str
    city: str
    screen_name: str
