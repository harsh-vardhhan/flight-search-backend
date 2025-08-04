import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase

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

def get_text_to_sql_chain(db: SQLDatabase):
    """
    Creates a LangChain chain that converts a natural language query into an SQL query.
    Uses a custom prompt to ensure clean SQL output without prefixes.
    """
    # Create a custom prompt for cleaner SQL generation
    custom_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a SQL expert. Given the database schema below, write a SQL query to answer the user's question.

Database Schema:
{schema}

IMPORTANT RULES:
1. Return ONLY the SQL query, no explanations, no prefixes like "SQLQuery:" or "SQL:"
2. Do NOT use quotes around column names unless absolutely necessary
3. Use proper SQLite syntax
4. The table name is 'flight'
5. Common columns include: airline, origin, destination, price_inr, date, flight_number, departure_time, arrival_time
6. For price comparisons, use price_inr column
7. For sorting by price (cheapest first), use ORDER BY price_inr ASC
8. When limiting results, use LIMIT with an appropriate number (like 5 or 10)

Return only the SQL query:"""),
        ("human", "{question}")
    ])
    
    # Create a custom chain that uses our prompt
    def get_schema(_):
        return db.get_table_info()
    
    chain = {
        "schema": get_schema,
        "question": lambda x: x["question"]
    } | custom_prompt | llm | StrOutputParser()
    
    return chain