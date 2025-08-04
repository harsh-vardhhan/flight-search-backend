# schemas.py

from pydantic import BaseModel
from datetime import date

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

class ApiResponse(BaseModel):
    status: str
    query_type: str
    sql_query: str | None = None
    data: list[FlightBase] | str