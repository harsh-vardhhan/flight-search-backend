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


# --- UPDATED: The function now also accepts an 'after_date' parameter ---
def get_flights_by_params(
    db: Session,
    origin: str,
    destination: str,
    limit: int,
    on_date: Optional[date] = None,
    after_date: Optional[date] = None # <-- NEW PARAMETER
) -> list[models.Flight]:
    """
    Safely queries for flights, now with an optional 'on_date' for exact matches
    or 'after_date' for finding the cheapest flight after a specific date.
    """
    query = (
        db.query(models.Flight)
        .filter(models.Flight.origin == origin, models.Flight.destination == destination)
    )

    # Add the date filter based on the provided parameters
    if on_date:
        # Use for exact date matches
        query = query.filter(models.Flight.date == on_date)
    elif after_date:
        # <-- NEW LOGIC
        # Use for finding the cheapest flight *after* a specific date
        query = query.filter(models.Flight.date > after_date)

    return query.order_by(models.Flight.price_inr.asc()).limit(limit).all()

# ... (keep the old execute_sql_query function if you wish) ...