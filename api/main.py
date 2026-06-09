from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Aria V2", version="2.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class ProfessionalOrchestrator:
    def execute(self, user_input: str):
        text = user_input.lower()
        if any(kw in text for kw in ["curso", "genera curso"]):
            return {"action": "execute_income", "result": {"message": "Curso generado", "price": 97}}
        if "ebook" in text:
            return {"action": "execute_income", "result": {"message": "Ebook generado", "price": 47}}
        if "mejora" in text:
            return {"action": "self_improve", "result": {"message": "Auto-mejora activada"}}
        return {"action": "respond", "result": {"message": f"Procesado: {user_input}"}}

orchestrator = ProfessionalOrchestrator()

@app.get("/", response_class=HTMLResponse)
async def home():
    try:
        with open(os.path.join(os.path.dirname(__file__), "../static/index.html")) as f:
            return HTMLResponse(f.read())
    except:
        return HTMLResponse("<h1>Aria V2</h1>")

@app.post("/api/chat")
async def chat(message: str = Form(...)):
    return orchestrator.execute(message)

@app.get("/api/health")
async def health():
    return {"status": "ok"}