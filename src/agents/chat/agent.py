import logging
import os
from typing import Any, Dict, AsyncGenerator
import anthropic
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class ChatAgent(BaseAgentV3):
    """
    ChatAgent - Conversacion real con Claude Sonnet.
    Soporta streaming SSE, memoria de conversacion y multiples modos.
    """

    def __init__(self):
        super().__init__(name="ChatAgent", model="claude-sonnet-4-20250514")
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.conversation_history = []
        self.system_prompt = """Eres Aria, una agente de IA de nivel competitivo creada en Saraph.
No eres un chatbot - eres un agente que actua: ejecutas codigo, creas repos, deploys y archivos reales.
Responde en espanol de forma directa, inteligente y sin rodeos.
Cuando el usuario pida algo accionable, confirma que lo estas ejecutando y describe los pasos."""

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        context = context or {}
        user_message = context.get("message", task)
        logger.info(f"{self.name} processing: {user_message[:80]}")

        self.conversation_history.append({"role": "user", "content": user_message})

        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=self.conversation_history
            ) as stream:
                full_response = ""
                for text in stream.text_stream:
                    full_response += text
                    yield f"data: {text}\n\n"

            self.conversation_history.append({"role": "assistant", "content": full_response})
            if len(self.conversation_history) > 40:
                self.conversation_history = self.conversation_history[-40:]

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            yield f"data: [ERROR] API error: {str(e)}\n\n"
        except Exception as e:
            logger.error(f"ChatAgent error: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"

    def clear_history(self):
        self.conversation_history = []
