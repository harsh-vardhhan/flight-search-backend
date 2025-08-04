from fastapi import FastAPI
from pydantic import BaseModel

# Create a FastAPI app instance
app = FastAPI()

# Define the request body model using Pydantic
# This ensures the incoming data has the correct structure
class Transcript(BaseModel):
    text: str

# Define a root endpoint for basic testing
@app.get("/")
def read_root():
    """A simple GET endpoint to check if the server is running."""
    return {"message": "RupeeTravel Backend is running"}

# Define the endpoint to receive the transcript
@app.post("/transcript")
def process_transcript(transcript: Transcript):
    """
    Receives a transcript from the mobile app, prints it,
    and returns a confirmation message.
    """
    print(f"Received transcript: '{transcript.text}'")
    # In a real app, you would process this text here (e.g., with a RAG model)
    return {
        "status": "success",
        "received_text": transcript.text,
        "reply": "Transcript received successfully!"
    }

# --- To Run This Server ---
# 1. Save this file as main.py
# 2. Make sure you have FastAPI and Uvicorn installed:
#    pip install fastapi uvicorn
# 3. Run from your terminal:
#    uvicorn main:app --host 0.0.0.0 --port 8000
#
# Your phone must be on the same Wi-Fi network as your computer.
# Find your computer's local IP address (e.g., 192.168.1.10)
# The mobile app will send requests to http://<YOUR_LOCAL_IP>:8000/transcript
