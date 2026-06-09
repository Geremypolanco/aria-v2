from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os, sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.orchestrator import orchestrator
from src.auth.router import router as auth_router

app = FastAPI(title="Aria V2 - Professional", version="2.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_router)

@app.get("/", response_class=HTMLResponse)
async def home():
    try:
        with open(os.path.join(os.path.dirname(__file__), "../static/index.html"), encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        return HTMLResponse(f"<h1>Aria V2</h1><p>Error loading frontend: {str(e)}</p>")

@app.post("/api/chat")
async def chat(message: str = Form(...)):
    try:
        result = orchestrator.execute(message)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "2.0"}