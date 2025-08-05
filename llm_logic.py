# llm_logic.py

from typing import Literal, Optional
from datetime import date, timedelta
import calendar
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Your Ollama LLM initialization (unchanged)
llm = ChatOllama(
            model="qwen3:4b",
            temperature=0.2,
        )

# Pydantic model (unchanged)
class FlightSearchParameters(BaseModel):
    trip_type: Literal["one_way", "round_trip"] = Field(..., description="The type of trip. Must be 'one_way' or 'round_trip'.")
    origin: str = Field(..., description="The starting city or airport for the flight. This is a required field.")
    destination: str = Field(..., description="The destination city or airport for the flight. This is a required field.")
    departure_date_start: Optional[str] = Field(None)
    departure_date_end: Optional[str] = Field(None)
    trip_duration_days: Optional[int] = Field(None)
    limit_per_leg: int = Field(1)

def get_intent_extraction_chain():
    """
    Creates a chain that extracts flight search parameters, including date ranges.
    """
    structured_llm = llm.with_structured_output(FlightSearchParameters)

    today = date.today()
    
    # --- FIX: Format the month information into a safe, readable string ---
    month_lengths_parts = []
    for i in range(1, 13):
        month_name = date(today.year, i, 1).strftime('%B')
        days_in_month = calendar.monthrange(today.year, i)[1]
        month_lengths_parts.append(f"{month_name}={days_in_month} days")
    month_lengths_str = ", ".join(month_lengths_parts)
    # This creates a string like: "January=31 days, February=28 days, ..."
    # This string has no curly braces and is safe for the prompt template.

    # --- UPDATED SYSTEM PROMPT using the safe string ---
    system_prompt = f"""
You are an expert at understanding user requests for flights and extracting them into a structured format.
The current date is {today.strftime('%Y-%m-%d')}. The current year is {today.year}.
Helpful context on month lengths: {month_lengths_str}.

DATE RANGE RULES:
Your goal is to populate 'departure_date_start' and 'departure_date_end'.

1.  **General Queries (No Date):** If the user asks for 'the cheapest flight' without any date context, leave both start and end dates as null.
2.  **Specific Date Queries:** If the user gives a specific day like 'tomorrow' or 'August 10th', set both start and end dates to that same date.
    - 'today': {today.strftime('%Y-%m-%d')}
    - 'tomorrow': {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
3.  **Month-Based Queries:** If the user gives a month like 'in December', set the start date to the 1st of that month and the end date to the last day of that month.
    - Example: "in December" -> start: '{today.year}-12-01', end: '{today.year}-12-31'
4.  **Week-Based Queries:** If the user says 'next week', calculate the start (next Monday) and end (next Sunday) of that week.

OTHER RULES:
- "a week long trip" or "weak long trip" means trip_duration_days should be 7.
- "cheapest" implies limit_per_leg should be 1.
- Try to correct obvious city name misspellings if possible (e.g., 'He knowing' might be 'Hanoi').
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{query}"),
        ]
    )
    
    return prompt | structured_llm
