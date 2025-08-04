# llm_logic.py

import os
from datetime import date
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Literal, Optional

# ... (keep LLM initialization the same) ...
load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY not found in .env file")
llm = ChatGroq(
    temperature=0,
    model_name="qwen/qwen3-32b",
    api_key=os.getenv("GROQ_API_KEY")
)


# --- UPDATED: Pydantic model with clearer description ---
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
        None, description="The departure date in YYYY-MM-DD format. Only extract if the user explicitly mentions a date." # <-- Modified description
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

    # --- UPDATED SYSTEM PROMPT to be more precise about dates ---
    system_prompt = f"""
You are an expert at understanding user requests for flights and extracting the key parameters into a structured format.
The current date is {date.today().strftime('%Y-%m-%d')}.

IMPORTANT DATE RULE: Only extract a date for 'start_date' if the user explicitly mentions one (e.g., 'today', 'tomorrow', 'next week', 'on August 10th'). If the user just asks for 'the cheapest flight' without mentioning a date, leave the 'start_date' field as null.

- If the user asks for a trip of a certain duration (e.g., "7 day trip"), extract that number into trip_duration_days.
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