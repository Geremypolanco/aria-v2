import os
import sys
import logging

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from src.core.orchestrator.v3 import orchestrator_v3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aria_v3")

app = FastAPI(title="ARIA ENGINE v3.0", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(os.path.dirname(__file__), "../static/index.html")
    if os.path.exists(html_path):
        with open(html_path, encoding="utf-8") as f:
            return HTMLResponse(f.read())
    return HTMLResponse("<h1>ARIA ENGINE v3.0</h1><p>Static frontend not found.</p>")

@app.post("/api/chat")
async def chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    
    logger.info(f"Received message: {message}")
    
    return StreamingResponse(
        orchestrator_v3.run(message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "3.0.0", "engine": "megan-v3"}
