# schemas.py

from pydantic import BaseModel, Field
from datetime import date
from typing import Literal, Optional

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

# --- This is the correct and only location for this class ---
class FlightSearchParameters(BaseModel):
    """
    The structured representation of the user's flight search query intent.
    """
    # Make essential fields optional so the LLM can ask for clarification
    trip_type: Optional[Literal["one_way", "round_trip"]] = Field(None)
    origin: Optional[str] = Field(None)
    destination: Optional[str] = Field(None)
    
    # Optional fields for more detailed queries
    departure_date_start: Optional[str] = Field(None)
    departure_date_end: Optional[str] = Field(None)
    trip_duration_days: Optional[int] = Field(None)
    limit_per_leg: int = Field(1, description="Defaults to 1 for 'cheapest'.")

    # Field for the LLM to ask for more info
    clarification_needed: Optional[str] = Field(
        None, description="If essential information is missing, provide a question for the user here."
    )

class ApiResponse(BaseModel):
    status: str
    query_type: str
    sql_query: str | None = None
    data: list[FlightBase] | str | FlightSearchParameters