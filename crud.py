# crud.py

import json
from datetime import datetime, date
from typing import Optional
import re
from sqlalchemy.orm import Session
import models

# ... (keep to_snake_case and populate_db_from_json as they are) ...
def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def populate_db_from_json(db: Session, json_path: str = "flight-price.json"):
    if db.query(models.Flight).count() > 0:
        print("Database already populated. Skipping population.")
        return
    db.query(models.Flight).delete()
    db.commit()
    print("Flight table cleared.")
    with open(json_path, 'r') as f:
        flight_data = json.load(f)
    for flight_dict in flight_data:
        if 'date' in flight_dict:
            flight_dict['date'] = datetime.strptime(flight_dict['date'], '%Y-%m-%d').date()
        snake_case_dict = {to_snake_case(k): v for k, v in flight_dict.items()}
        db_flight = models.Flight(**snake_case_dict)
        db.add(db_flight)
    db.commit()
    print(f"Successfully populated DB with {len(flight_data)} records.")


def get_flights_by_params(
    db: Session,
    origin: str,
    destination: str,
    limit: int,
    departure_start: Optional[date] = None, # <-- NEW
    departure_end: Optional[date] = None,   # <-- NEW
    after_date: Optional[date] = None
) -> list[models.Flight]:
    """
    Safely queries for flights.
    - If departure_start and departure_end are provided, it searches within that range.
    - If only after_date is provided, it searches for return flights after that date.
    """
    query = (
        db.query(models.Flight)
        .filter(models.Flight.origin == origin, models.Flight.destination == destination)
    )

    # --- NEW DATE FILTERING LOGIC ---
    if departure_start and departure_end:
        if departure_start == departure_end:
            # If start and end are the same, it's a query for an exact date
            query = query.filter(models.Flight.date == departure_start)
        else:
            # If they are different, it's a range query
            query = query.filter(models.Flight.date.between(departure_start, departure_end))
    elif after_date:
        # This is used for the return leg
        query = query.filter(models.Flight.date > after_date)
    
    # If no date parameters are given, it searches all dates (for "cheapest overall").

    return query.order_by(models.Flight.price_inr.asc()).limit(limit).all()