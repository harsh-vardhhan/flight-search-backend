# llm_logic.py

import os
from datetime import date
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Literal, Optional

# Load environment variables from .env file
load_dotenv()

# Ensure the GROQ_API_KEY is set
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file")

# Initialize the Groq LLM
llm = ChatGroq(
    temperature=0,
    model_name="qwen/qwen3-32b",
    api_key=os.getenv("GROQ_API_KEY")
)

# --- UPDATED: Pydantic model with date and duration fields ---
class FlightSearchParameters(BaseModel):
    """
    A structured representation of a user's flight search query.
    """
    trip_type: Literal["one_way", "round_trip"] = Field(
        ..., description="The type of trip the user wants. Inferred from the query."
    )
    origin: str = Field(..., description="The starting city or airport for the flight.")
    destination: str = Field(..., description="The destination city or airport for the flight.")
    start_date: Optional[str] = Field(
        None, description="The departure date in YYYY-MM-DD format. Inferred from query. Defaults to today if not specified."
    )
    trip_duration_days: Optional[int] = Field(
        None, description="The duration of the trip in days, used to calculate the return date for round trips."
    )
    limit_per_leg: int = Field(
        1, description="The number of flights to return per leg. 'cheapest' implies 1."
    )

# --- UPDATED: The chain now gets the current date to understand context ---
def get_intent_extraction_chain():
    """
    Creates a LangChain chain that extracts flight search parameters from a user query
    into a structured Pydantic object.
    """
    structured_llm = llm.with_structured_output(FlightSearchParameters)

    # UPDATED SYSTEM PROMPT to handle dates and durations
    system_prompt = f"""
You are an expert at understanding user requests for flights and extracting the key parameters into a structured format.
The current date is {date.today().strftime('%Y-%m-%d')}. Use this for any relative date calculations (e.g., 'today', 'tomorrow').

- If the user asks for a trip of a certain duration (e.g., "7 day trip", "weekend trip for 2 days"), extract that number into trip_duration_days.
- If the user specifies a departure date, extract it into start_date in YYYY-MM-DD format. If they don't, you can leave it as null.
- If the user mentions traveling from A to B and also back from B to A, the trip_type is 'round_trip'.
- If the user only mentions a one-way journey from A to B, the trip_type is 'one_way'.
- "cheapest" implies a limit of 1.
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{query}"),
        ]
    )
    
    chain = prompt | structured_llm
    
    return chain