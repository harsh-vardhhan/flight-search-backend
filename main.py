# main.py

from contextlib import asynccontextmanager
from datetime import date, timedelta, datetime
import calendar
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import ValidationError

import crud
import models
import schemas
import llm_logic
from database import SessionLocal, engine
from query_classifier import is_flight_related_query
import logfire

# Create database tables on startup
models.Base.metadata.create_all(bind=engine)

# Initialize the LangChain chain
intent_extraction_chain = llm_logic.get_intent_extraction_chain()

# --- Application Lifespan (Startup/Shutdown Events) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup logic. In this case, it populates the database.
    """
    print("Application startup...")
    db = SessionLocal()
    try:
        crud.populate_db_from_json(db)
    finally:
        db.close()
    yield
    print("Application shutdown...")

# Create the FastAPI app instance with the lifespan manager
app = FastAPI(lifespan=lifespan)
logfire.configure()  
logfire.info('Hello, {name}!', name='world') 
logfire.instrument_fastapi(app)

# --- Dependency to get a database session for each request ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Helper function to apply logic-based corrections to the LLM's output ---
def refine_intent_with_guardrails(query: str, params: schemas.FlightSearchParameters) -> schemas.FlightSearchParameters:
    """
    Catches common LLM extraction errors and corrects them using Python logic.
    This acts as a "guardrail" to improve reliability.
    """
    query_lower = query.lower()
    
    # Guardrail 1: If the user mentioned a month but the LLM missed it, fix it here.
    if params.departure_date_start is None:
        today = date.today()
        month_map = {month.lower(): i for i, month in enumerate(calendar.month_name) if month}

        for month_name, month_num in month_map.items():
            if month_name in query_lower:
                print(f"--- GUARDRAIL ACTIVATED: Correcting missing month: {month_name.title()} ---")
                
                year = today.year
                if month_num < today.month:
                    year += 1 
                
                first_day = date(year, month_num, 1)
                last_day_num = calendar.monthrange(year, month_num)[1]
                last_day = date(year, month_num, last_day_num)
                
                # Override the LLM's faulty output
                params.departure_date_start = first_day.strftime('%Y-%m-%d')
                params.departure_date_end = last_day.strftime('%Y-%m-%d')
                break
    
    return params


# --- Main API Endpoint ---
@app.post("/transcript", response_model=schemas.ApiResponse)
async def handle_transcript(
    request: schemas.TranscriptRequest, db: Session = Depends(get_db)
):
    """
    Processes the user's query, extracts intent, and fetches flight data.
    """
    user_query = request.text
    print(f"Received query: {user_query}")

    is_flight_related = is_flight_related_query(user_query)
    query_type = "flight_related" if is_flight_related else "other"
    print(f"Classified as: {query_type}")

    if is_flight_related:
        try:
            # Step 1: Get the initial intent from the LLM
            params = await intent_extraction_chain.ainvoke({"query": user_query})
            print(f"Extracted Intent: {params}")

            # Step 2: Apply guardrails to fix potential LLM mistakes
            params = refine_intent_with_guardrails(user_query, params)
            print(f"Refined Intent: {params}")

            # Step 3: Proceed with the corrected parameters to find flights
            all_flights = []
            
            dep_start = datetime.strptime(params.departure_date_start, '%Y-%m-%d').date() if params.departure_date_start else None
            dep_end = datetime.strptime(params.departure_date_end, '%Y-%m-%d').date() if params.departure_date_end else None

            outbound_flights = crud.get_flights_by_params(
                db=db,
                origin=params.origin,
                destination=params.destination,
                limit=params.limit_per_leg,
                departure_start=dep_start,
                departure_end=dep_end
            )

            if outbound_flights:
                all_flights.extend(outbound_flights)
                actual_outbound_date = outbound_flights[0].date

                if params.trip_type == "round_trip":
                    if params.trip_duration_days:
                        return_target_date = actual_outbound_date + timedelta(days=params.trip_duration_days)
                        inbound_flights = crud.get_flights_by_params(
                            db=db, origin=params.destination, destination=params.origin,
                            limit=params.limit_per_leg, departure_start=return_target_date, departure_end=return_target_date
                        )
                        if inbound_flights: all_flights.extend(inbound_flights)
                    else:
                        inbound_flights = crud.get_flights_by_params(
                            db=db, origin=params.destination, destination=params.origin,
                            limit=params.limit_per_leg, after_date=actual_outbound_date
                        )
                        if inbound_flights: all_flights.extend(inbound_flights)
            
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
                data=all_flights if all_flights else "I searched, but couldn't find any flights matching your criteria."
            )

        except ValidationError as e:
            print(f"LLM failed to extract required fields: {e}")
            return schemas.ApiResponse(
                status="error",
                query_type="understanding_error",
                data="I'm sorry, I couldn't understand your request. Please make sure to state your origin, destination, and if it's a one-way or round trip."
            )
        
        except Exception as e:
            print(f"An unexpected error occurred in the flight query logic: {e}")
            return schemas.ApiResponse(
                status="error",
                query_type="server_error",
                data="Sorry, I encountered an internal error. Please try again."
            )
            
    else:
        return schemas.ApiResponse(
            status="success",
            query_type="other",
            data="This assistant can only help with flight-related queries."
        )

# --- Root endpoint for health checks ---
@app.get("/")
def read_root():
    return {"message": "RupeeTravel RAG Backend is running"}