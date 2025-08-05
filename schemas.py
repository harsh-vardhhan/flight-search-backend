# schemas.py

from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field

class TranscriptRequest(BaseModel):
    text: str

class FlightBase(BaseModel):
    id: int
    uuid: str
    date: date
    origin: str
    destination: str
    airline: str
    duration: str
    flight_type: str
    price_inr: int
    link: str

    class Config:
        from_attributes = True

# --- NEW: Moved from llm_logic.py to its correct home ---
class FlightSearchParameters(BaseModel):
    """
    The structured representation of the user's flight search query intent.
    """
    trip_type: Literal["one_way", "round_trip"] = Field(..., description="The type of trip. Must be 'one_way' or 'round_trip'.")
    origin: str = Field(..., description="The starting city or airport for the flight. This is a required field.")
    destination: str = Field(..., description="The destination city or airport for the flight. This is a required field.")
    departure_date_start: Optional[str] = Field(None)
    departure_date_end: Optional[str] = Field(None)
    trip_duration_days: Optional[int] = Field(None)
    limit_per_leg: int = Field(1)


class ApiResponse(BaseModel):
    status: str
    query_type: str
    sql_query: str | None = None
    data: list[FlightBase] | str | FlightSearchParameters # Allow data to also be the search params for debugging if needed