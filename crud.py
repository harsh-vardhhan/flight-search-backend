# crud.py

import json
from datetime import datetime, date # Make sure date is imported
from typing import Optional # Import Optional
import re
from sqlalchemy.orm import Session
from sqlalchemy import text
import models

# ... (keep to_snake_case and populate_db_from_json as they are) ...
def to_snake_case(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def populate_db_from_json(db: Session, json_path: str = "flight-data.json"):
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


# --- UPDATED: The safe query function now accepts an optional date ---
def get_flights_by_params(
    db: Session, 
    origin: str, 
    destination: str, 
    limit: int, 
    on_date: Optional[date] = None
) -> list[models.Flight]:
    """
    Safely queries for flights, now with an optional date filter.
    """
    query = (
        db.query(models.Flight)
        .filter(models.Flight.origin == origin, models.Flight.destination == destination)
    )
    
    # Add the date filter only if a date is provided
    if on_date:
        query = query.filter(models.Flight.date == on_date)
        
    return query.order_by(models.Flight.price_inr.asc()).limit(limit).all()

# ... (keep the old execute_sql_query function if you wish, but it's not used here) ...