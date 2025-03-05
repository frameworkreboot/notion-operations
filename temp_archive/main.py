"""
Entrypoint for the FastAPI application.

This file:
1. Creates the FastAPI app.
2. Exposes the endpoint that Notion will call via a webhook.
3. Delegates to 'webhook_handler' for the actual processing logic.
"""

from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import os
import uvicorn
from .webhook_handler import process_notion_webhook
from .notion_api import NotionAPI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

app = FastAPI(title="Notion-CrewAI Orchestrator")
notion_api = NotionAPI(
    notion_api_key=os.getenv("NOTION_API_KEY"),
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

@app.post("/notion-webhook")
async def notion_webhook(request: Request) -> dict:
    """
    Receives inbound HTTP POST requests from Notion.
    
    Args:
        request (Request): The FastAPI request object containing the JSON payload.
    
    Returns:
        dict: A JSON response summarizing what happened with the request.
    """
    try:
        payload = await request.json()
        logging.info(f"Received webhook payload: {payload}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON payload: {e}")
    
    try:
        result = await process_notion_webhook(payload, notion_api)
        return {"status": "success", "result": result}
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/notion-webhook")
async def notion_webhook_health():
    """Notion requires the webhook URL to respond to GET requests"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)