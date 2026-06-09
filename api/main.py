from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.agent import run_agent_stream
from src.auth.router import router as auth_router
from src.auth.dependencies import get_current_user
from src.db.repositories import ConversationRepository
from src.core.config import settings

app = FastAPI(title="Aria V2", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET)
app.include_router(auth_router)


class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None


@app.get("/", response_class=HTMLResponse)
async def home():
    path = os.path.join(os.path.dirname(__file__), "../static/index.html")
    with open(path, encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.post("/api/chat")
async def chat(
    req: ChatRequest,
    user: dict = Depends(get_current_user),
):
    user_id = user["sub"]

    # Cargar o crear conversación
    conv_id = req.conversation_id
    if conv_id:
        messages = await ConversationRepository.get_messages(conv_id, user_id)
    else:
        conv_id = await ConversationRepository.create(user_id)
        messages = []

    messages.append({"role": "user", "content": req.message})
    await ConversationRepository.add_message(conv_id, "user", req.message)

    async def stream_response():
        full_response = ""
        async for chunk in run_agent_stream(messages, user_id):
            yield chunk
            if (
                chunk.startswith("data: ")
                and not chunk.startswith("data: [DONE]")
                and not chunk.startswith("data: __tool__")
            ):
                full_response += chunk[6:].strip()

        if full_response:
            await ConversationRepository.add_message(conv_id, "assistant", full_response)

        yield f"data: __conv_id__{conv_id}__\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={"X-Conversation-Id": conv_id},
    )


@app.get("/api/conversations")
async def get_conversations(user: dict = Depends(get_current_user)):
    return await ConversationRepository.list(user["sub"])


@app.get("/api/health")
async def health():
    return {"status": "healthy", "version": "2.0"}
