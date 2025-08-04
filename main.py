# main.py

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from datetime import date, timedelta, datetime # Import date, timedelta, datetime

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
    # ... (lifespan function remains the same) ...
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
    # ... (get_db function remains the same) ...
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- UPDATED: The main endpoint with date handling logic ---
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

            # --- NEW DATE LOGIC ---
            # 1. Determine the outbound date. Default to today if not specified by the LLM.
            outbound_date = None
            if params.start_date:
                outbound_date = datetime.strptime(params.start_date, '%Y-%m-%d').date()
            else:
                outbound_date = date.today() # Default to today
            
            # 2. Find the outbound flight
            outbound_flights = crud.get_flights_by_params(
                db=db,
                origin=params.origin,
                destination=params.destination,
                limit=params.limit_per_leg,
                on_date=outbound_date # Pass the date to the query
            )
            if outbound_flights:
                all_flights.extend(outbound_flights)

            # 3. For round trips, calculate return date and find the return flight
            if params.trip_type == "round_trip":
                return_date = None
                # Calculate return date if duration is known
                if params.trip_duration_days:
                    return_date = outbound_date + timedelta(days=params.trip_duration_days)

                inbound_flights = crud.get_flights_by_params(
                    db=db,
                    origin=params.destination,
                    destination=params.origin,
                    limit=params.limit_per_leg,
                    on_date=return_date # Pass the calculated return date
                )
                if inbound_flights:
                    all_flights.extend(inbound_flights)
            
            # (Your debugging print statement from before)
            print("\n--- [DEBUG] Final Flights to be Returned ---")
            if not all_flights:
                print("No flights found on the specified dates.")
            else:
                for i, flight in enumerate(all_flights):
                    print(
                        f"  Flight {i+1}: "
                        f"Date='{flight.date}', "
                        f"Origin='{flight.origin}', "
                        f"Destination='{flight.destination}', "
                        f"Price=₹{flight.price_inr}"
                    )
            print("--------------------------------------------\n")

            return schemas.ApiResponse(
                status="success",
                query_type="flight_related",
                sql_query=f"Intent: {str(params)}",
                data=all_flights,
            )
        except Exception as e:
            print(f"An error occurred in the flight query logic: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred in the flight query logic: {e}"
            )

    else:
        return schemas.ApiResponse(
            status="success",
            query_type="other",
            data="This assistant can only help with flight-related queries.",
        )

# ... (keep the rest of your main.py file) ...