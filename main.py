# main.py

from contextlib import asynccontextmanager
from datetime import timedelta, datetime
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import models
import schemas
import llm_logic
from database import SessionLocal, engine
from query_classifier import is_flight_related_query

models.Base.metadata.create_all(bind=engine)
intent_extraction_chain = llm_logic.get_intent_extraction_chain()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup...")
    db = SessionLocal()
    try:
        crud.populate_db_from_json(db)
    finally:
        db.close()
    yield
    print("Application shutdown...")

app = FastAPI(lifespan=lifespan)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/transcript", response_model=schemas.ApiResponse)
async def handle_transcript(
    request: schemas.TranscriptRequest, db: Session = Depends(get_db)
):
    user_query = request.text
    print(f"Received query: {user_query}")

    is_flight_related = is_flight_related_query(user_query)
    query_type = "flight_related" if is_flight_related else "other"
    print(f"Classified as: {query_type}")

    if is_flight_related:
        try:
            params = await intent_extraction_chain.ainvoke({"query": user_query})
            print(f"Extracted Intent: {params}")

            all_flights = []

            # --- UPDATED DATE LOGIC TO USE RANGES ---
            dep_start = datetime.strptime(params.departure_date_start, '%Y-%m-%d').date() if params.departure_date_start else None
            dep_end = datetime.strptime(params.departure_date_end, '%Y-%m-%d').date() if params.departure_date_end else None

            # Find the cheapest outbound flight within the specified range (or on any date if range is None)
            outbound_flights = crud.get_flights_by_params(
                db=db,
                origin=params.origin,
                destination=params.destination,
                limit=params.limit_per_leg,
                departure_start=dep_start, # Pass the range start
                departure_end=dep_end      # Pass the range end
            )

            # (The return logic remains the same, as it's already robust)
            if outbound_flights:
                all_flights.extend(outbound_flights)
                actual_outbound_date = outbound_flights[0].date

                if params.trip_type == "round_trip":
                    if params.trip_duration_days:
                        return_target_date = actual_outbound_date + timedelta(days=params.trip_duration_days)
                        inbound_flights = crud.get_flights_by_params(
                            db=db, origin=params.destination, destination=params.origin,
                            limit=params.limit_per_leg, departure_start=return_target_date, departure_end=return_target_date # Search for an exact date
                        )
                        if inbound_flights: all_flights.extend(inbound_flights)
                    else:
                        inbound_flights = crud.get_flights_by_params(
                            db=db, origin=params.destination, destination=params.origin,
                            limit=params.limit_per_leg, after_date=actual_outbound_date # Search after the outbound date
                        )
                        if inbound_flights: all_flights.extend(inbound_flights)
            
            # (Debugging print statement)
            print("\n--- [DEBUG] Final Flights to be Returned ---")
            if not all_flights:
                print("No flights found matching the criteria.")
            else:
                for i, flight in enumerate(all_flights):
                    print(f"  Flight {i+1}: Date='{flight.date}', Origin='{flight.origin}', Destination='{flight.destination}', Price=₹{flight.price_inr}")
            print("--------------------------------------------\n")

            return schemas.ApiResponse(
                status="success",
                query_type="flight_related",
                sql_query=f"Intent: {str(params)}",
                data=all_flights,
            )
        except Exception as e:
            # ... (error handling) ...
            print(f"An error occurred in the flight query logic: {e}")
            raise HTTPException(status_code=500, detail=f"An error occurred in the flight query logic: {e}")
    else:
        # ... (other logic) ...
        return schemas.ApiResponse(status="success", query_type="other", data="This assistant can only help with flight-related queries.")