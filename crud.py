import json
from datetime import datetime
import re
from sqlalchemy.orm import Session
from sqlalchemy import text
import models

def to_snake_case(name):
    """Converts a camelCase string to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def populate_db_from_json(db: Session, json_path: str = "flight-data.json"):
    """
    Clears the flight table and populates it with data from a JSON file.
    """
    # Clear existing data
    db.query(models.Flight).delete()
    db.commit()
    print("Flight table cleared.")

    # Load data from JSON file
    with open(json_path, 'r') as f:
        flight_data = json.load(f)

    # Add new records
    for flight_dict in flight_data:
        # Convert date string to date object
        if 'date' in flight_dict:
            flight_dict['date'] = datetime.strptime(flight_dict['date'], '%Y-%m-%d').date()
        
        # Convert all keys from camelCase to snake_case to match the model
        snake_case_dict = {to_snake_case(k): v for k, v in flight_dict.items()}
        
        # Create the Flight object using the corrected dictionary
        db_flight = models.Flight(**snake_case_dict)
        db.add(db_flight)
    
    db.commit()
    print(f"Successfully populated DB with {len(flight_data)} records.")

def execute_sql_query(db: Session, sql_query: str):
    """
    Executes a raw SQL query and returns the results.
    """
    try:
        result = db.execute(text(sql_query))
        # Fetch all rows and convert them to a list of dictionaries
        rows = [row._asdict() for row in result.fetchall()]
        return rows
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return None
