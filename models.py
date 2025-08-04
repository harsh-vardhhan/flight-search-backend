# models.py
from sqlalchemy import Boolean, Column, Integer, String, Float, Date
from sqlalchemy.types import Date as SQLDate
from database import Base

class Flight(Base):
    __tablename__ = "flight"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True)
    date = Column(SQLDate)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    airline = Column(String, index=True)
    duration = Column(String)
    flight_type = Column(String)
    price_inr = Column(Integer, index=True)
    origin_country = Column(String)
    destination_country = Column(String)
    link = Column(String)
    rain_probability = Column(Integer)
    free_meal = Column(Boolean)
    min_checked_luggage_price = Column(Integer)
    min_checked_luggage_weight = Column(String)
    total_with_min_luggage = Column(Integer)
