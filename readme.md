# RupeeTravel - Conversational Query Interface

RupeeTravel is a backend API for conversational flight search, powered by an LLM and a local flight database. Users can interact using natural language queries to find flights, get prices, and specify trip details.

## Features

- **Conversational Flight Search:** Accepts free-form queries (e.g., "Find me the cheapest flights from Delhi to Hanoi in December").
- **LLM-Powered Intent Extraction:** Uses [Qwen3:1.7b](https://github.com/QwenLM/Qwen) via Ollama for robust query understanding.
- **Guardrails:** Python logic corrects common LLM extraction mistakes for reliability.
- **SQLite Database:** Stores flight data locally for fast queries.
- **FastAPI Backend:** RESTful API endpoints for integration.
- **Automatic Database Population:** Loads flight## Frontend

A companion frontend for RupeeTravel is available at:  
[https://github.com/harsh-vardhhan/flight-search-frontend](https://github.com/harsh-vardhhan/flight-search-frontend) data from `flight-price.json` on startup.

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **LLM:** Qwen3:1.7b via [Ollama](https://ollama.com/)
- **Database:** SQLite (`flight.db`)
- **ORM:** SQLAlchemy
- **Prompt Engineering:** LangChain
- **Environment Variables:** Managed via `.env`

## API Endpoints

- `POST /transcript`  
  Accepts a user query and returns matching flight options or clarification questions.

- `GET /`  
  Health check endpoint.

## File Structure

- `main.py` — FastAPI app and core logic
- `llm_logic.py` — LLM prompt and intent extraction chain
- `crud.py` — Database query functions
- `models.py` — SQLAlchemy models
- `schemas.py` — Pydantic schemas
- `database.py` — DB setup
- `flight-price.json` — Source flight data

## How It Works

1. **Startup:**  
   - Database tables are created.
   - Flight data is loaded from `flight-price.json`.

2. **Query Flow:**  
   - User sends a query to `/transcript`.
   - LLM extracts intent (origin, destination, dates, trip type, etc.).
   - Guardrails fix missing or ambiguous info.
   - Database is queried for matching flights.
   - Results or clarifications are returned.

## Setup

1. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

2. **Start Ollama with Qwen3:1.7b:**
   ```sh
   ollama pull qwen3:1.7b
   ollama serve
   ```

3. **Run the API:**
   ```sh
   uvicorn main:app --reload
   ```

## Environment Variables

Configure your `.env` file for any required secrets or LLM settings.

## License

MIT