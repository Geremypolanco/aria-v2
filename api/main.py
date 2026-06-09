"""
Aria V2 — Main FastAPI application.
Entry point for Vercel serverless deployment.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel

from src.core.config import settings
from src.core.agent import run_agent
from src.auth.router import router as auth_router
from src.auth.dependencies import get_current_user
from src.db.repositories import ConversationRepository

# ─────────────────────────────────────────────
app = FastAPI(title="Aria V2", version="2.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)
app.include_router(auth_router)


# ─────────────────────────────────────────────
# Static frontend
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def home():
    html_path = os.path.join(os.path.dirname(__file__), "../static/index.html")
    with open(html_path, encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ─────────────────────────────────────────────
# Chat — streaming SSE
# ─────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


@app.post("/api/chat")
async def chat(
    req: ChatRequest,
    user: dict = Depends(get_current_user),
):
    user_id = user["sub"]

    # Load or create conversation
    if req.conversation_id:
        messages = ConversationRepository.get_messages(req.conversation_id, user_id)
        conv_id = req.conversation_id
    else:
        conv_id = ConversationRepository.create(user_id)
        messages = []

    messages.append({"role": "user", "content": req.message})
    ConversationRepository.add_message(conv_id, "user", req.message)

    async def stream():
        full_response = ""
        async for chunk in run_agent(messages, user_id):
            yield chunk
            # Accumulate text chunks (not markers)
            if (
                chunk.startswith("data: ")
                and not chunk.startswith("data: [DONE]")
                and not chunk.startswith("data: __tool")
            ):
                full_response += chunk[6:].rstrip("\n")

        if full_response:
            ConversationRepository.add_message(conv_id, "assistant", full_response)

        yield f"data: __conv_id__{conv_id}__\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Conversation-Id": conv_id,
        },
    )


# ─────────────────────────────────────────────
# Conversations
# ─────────────────────────────────────────────
@app.get("/api/conversations")
async def get_conversations(user: dict = Depends(get_current_user)):
    return ConversationRepository.list(user["sub"])


@app.get("/api/conversations/{conv_id}/messages")
async def get_messages(conv_id: str, user: dict = Depends(get_current_user)):
    return ConversationRepository.get_messages(conv_id, user["sub"])


# ─────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "2.0.0", "agent": "aria"}
