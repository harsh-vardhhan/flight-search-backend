from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_community.utilities import SQLDatabase
from contextlib import asynccontextmanager

# CORRECTED: Changed relative imports to direct imports for the main entry file.
import crud
import models
import schemas
import llm_logic
from strip_think_tags import strip_think_tags
from clean_sql_query import clean_sql_query
from database import SessionLocal, engine
from query_classifier import is_flight_related_query  # Import the new classifier


# Create all database tables
models.Base.metadata.create_all(bind=engine)

# --- Database and LLM Chain Initialization ---
db_for_langchain = SQLDatabase(engine=engine)
# Remove the query classifier chain since we're using the function instead
text_to_sql_chain = llm_logic.get_text_to_sql_chain(db_for_langchain)


from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_community.utilities import SQLDatabase
from contextlib import asynccontextmanager

# CORRECTED: Changed relative imports to direct imports for the main entry file.
import crud
import models
import schemas
import llm_logic
from strip_think_tags import strip_think_tags
from clean_sql_query import clean_sql_query
from database import SessionLocal, engine
from query_classifier import is_flight_related_query  # Import the new classifier


# Create all database tables
models.Base.metadata.create_all(bind=engine)

# --- Database and LLM Chain Initialization ---
db_for_langchain = SQLDatabase(engine=engine)
# Remove the query classifier chain since we're using the function instead
text_to_sql_chain = llm_logic.get_text_to_sql_chain(db_for_langchain)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on application startup
    print("Application startup...")
    db = SessionLocal()
    try:
        crud.populate_db_from_json(db)
    finally:
        db.close()
    yield
    # This code runs on application shutdown
    print("Application shutdown...")


# Create the FastAPI app instance with the lifespan event handler
app = FastAPI(lifespan=lifespan)


# Dependency to get a database session
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
    """
    Main endpoint to process user's voice transcript.
    1. Classifies the query using fuzzy matching.
    2. If flight-related, generates and executes an SQL query.
    3. Returns the results.
    """
    user_query = request.text
    print(f"Received query: {user_query}")

    # 1. Classify the query using the new function
    is_flight_related = is_flight_related_query(user_query)
    query_type = "flight_related" if is_flight_related else "other"
    print(f"Classified as: {query_type}")

    # 2. Handle based on classification
    if is_flight_related:
        try:
            # Generate SQL query from the user's text
            sql_query_response = await text_to_sql_chain.ainvoke({"question": user_query})
            stripped_sql_query = strip_think_tags(sql_query_response)
            sql_query = clean_sql_query(stripped_sql_query)
            print(f"Generated SQL: {sql_query}")

            # Execute the SQL query
            results = crud.execute_sql_query(db, sql_query)
            
            if results is None:
                 raise HTTPException(status_code=500, detail="Failed to execute SQL query.")

            return schemas.ApiResponse(
                status="success",
                query_type="flight_related",
                sql_query=sql_query.strip(),
                data=results
            )
        except Exception as e:
            print(f"An error occurred in the flight query logic: {e}")
            return schemas.ApiResponse(
                status="error",
                query_type="flight_related",
                data=f"Sorry, I encountered an error processing your flight request: {e}"
            )
    else:
        # If not flight-related, return a simple message
        return schemas.ApiResponse(
            status="success",
            query_type="other",
            data="This assistant can only help with flight-related queries."
        )

@app.get("/")
def read_root():
    return {"message": "RupeeTravel RAG Backend is running"}