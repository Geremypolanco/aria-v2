from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.orchestrator import orchestrator
from src.auth.router import router as auth_router

app = FastAPI(title="Aria V2")
app.include_router(auth_router)

@app.get("/", response_class=HTMLResponse)
async def home():
    path = os.path.join(os.path.dirname(__file__), "../static/index.html")
    with open(path) as f: return HTMLResponse(f.read())

@app.post("/api/chat")
async def chat(message: str):
    return orchestrator.execute(message)