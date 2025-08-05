# llm_logic.py

from datetime import date, timedelta
from typing import Literal, Optional
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Your Ollama LLM initialization
llm = ChatOllama(
            model="qwen3:1.7b",
            temperature=0.2,
        )

# The Pydantic model remains the same
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
        None, description="The departure date in YYYY-MM-DD format. Only extract if the user explicitly mentions a date."
    )
    trip_duration_days: Optional[int] = Field(
        None, description="The duration of the trip in days, used to calculate the return date for round trips."
    )
    limit_per_leg: int = Field(
        1, description="The number of flights to return per leg. 'cheapest' implies 1."
    )

def get_intent_extraction_chain():
    """
    Creates a LangChain chain that extracts flight search parameters from a user query
    into a structured Pydantic object.
    """
    structured_llm = llm.with_structured_output(FlightSearchParameters)

    # --- UPDATED: System prompt with comprehensive date handling rules ---
    system_prompt = f"""
You are an expert at understanding user requests for flights and extracting the key parameters into a structured format.
The current date is {date.today().strftime('%Y-%m-%d')}. The current year is {date.today().year}.

DATE RULES:
1.  **Only extract a date for 'start_date' if the user explicitly mentions one.** If the user just asks for 'the cheapest flight' without mentioning a date, leave the 'start_date' field as null.
2.  **Handle relative dates:** 'today' is {date.today().strftime('%Y-%m-%d')}. 'tomorrow' is {(date.today() + timedelta(days=1)).strftime('%Y-%m-%d')}.
3.  **Handle month-based queries:** If the user mentions a month (e.g., "in December", "next January"), interpret the start_date as the first day of that month in the correct year. Given the current date, "in December" means '2025-12-01'. "Next January" would mean '2026-01-01'.

OTHER RULES:
- If the user asks for a trip of a certain duration (e.g., "a week long trip" means 7 days, "weekend trip" means 2 days), extract that number into trip_duration_days.
- If the user mentions traveling from A to B and back, the trip_type is 'round_trip'.
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