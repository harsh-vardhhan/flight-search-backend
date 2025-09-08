# llm_logic.py

from datetime import date, timedelta
import calendar
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
import schemas  # <-- CORRECT: Import the schemas module

# Load environment variables
load_dotenv()

# Your Ollama LLM initialization
llm = ChatOllama(
            model="qwen3:0.6b",
            temperature=0.2,
        )

def get_intent_extraction_chain():
    """
    Creates a chain that extracts flight search parameters into a structured object
    defined in schemas.py.
    """
    # CORRECT: Reference the class from the imported schemas module
    structured_llm = llm.with_structured_output(schemas.FlightSearchParameters)

    today = date.today()
    month_lengths_parts = []
    for i in range(1, 13):
        month_name = date(today.year, i, 1).strftime('%B')
        days_in_month = calendar.monthrange(today.year, i)[1]
        month_lengths_parts.append(f"{month_name}={days_in_month} days")
    month_lengths_str = ", ".join(month_lengths_parts)

    system_prompt = f"""
You are an expert at understanding user requests for flights and extracting them into a structured format.
The current date is {today.strftime('%Y-%m-%d')}.

SCHEMA FIELD RULES - FOLLOW EXACTLY:

1. trip_type: Must be EXACTLY 'one_way' or 'round_trip' (with underscore)
   - "round trip", "return", "return trip", "both ways" → 'round_trip'
   - "one way", "single", "just going" → 'one_way'
   - If trip type is NOT clearly specified, leave as null and ask for clarification

2. origin: Extract the departure city/airport
   - "from New Delhi" → "New Delhi"
   - "Delhi" → "New Delhi" (expand common abbreviations)

3. destination: Extract the arrival city/airport
   - "to Hanoi" → "Hanoi"

4. limit_per_leg: Number of flight options to return
   - "cheapest" → 1
   - "cheap", "budget", "lowest price" → 1
   - "options", "alternatives" → 3
   - Default: 3

5. For dates: Use YYYY-MM-DD format
   - "next week" → calculate actual dates
   - "in December" → 2024-12-01 to 2024-12-31
   - "tomorrow" → {(today + timedelta(days=1)).strftime('%Y-%m-%d')}

CLARIFICATION RULE:
If the user's query is missing essential information like 'origin', 'destination', or 'trip_type', you MUST NOT guess.
Instead, leave the missing fields as null and fill the 'clarification_needed' field with a friendly question asking for the missing information.

TRIP TYPE CLARIFICATION:
- If the query says "flight from X to Y" or "cheapest flight from X to Y" without specifying "round trip", "return", "one way", etc., this is AMBIGUOUS.
- You must ask: "Would you like a one-way flight or a round-trip flight from [origin] to [destination]?"

TRIP TYPE DETECTION LOGIC:
- ONLY set trip_type if the user explicitly mentions direction keywords
- Explicit round-trip indicators: "round trip", "return", "return trip", "both ways", "back and forth"
- Explicit one-way indicators: "one way", "single", "just going", "no return"
- If NO explicit trip type indicators are found, leave trip_type as null and ask for clarification

EXTRACTION RULES:
- If the query is complete, extract all the information into the other fields and leave 'clarification_needed' as null.
- For date ranges, use the context: "in December" means from Dec 1 to Dec 31. The current year is {today.year}. Month lengths: {month_lengths_str}.
- "a week long trip" means trip_duration_days should be 7.
- Always double-check that trip_type is exactly 'one_way' or 'round_trip' with underscore.
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{query}"),
        ]
    )
    
    return prompt | structured_llm