from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.orchestrator import orchestrator
from src.auth.router import router as auth_router

app = FastAPI(title="Aria V2")
app.include_router(auth_router)

@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(os.path.dirname(__file__), "../static/index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.post("/chat")
async def chat(message: str = Form(...)):
    result = orchestrator.execute(message)
    return result