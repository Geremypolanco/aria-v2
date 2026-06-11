import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class VoiceAgent(BaseAgentV3):
    def __init__(self):
        super().__init__(name="VoiceAgent", model="whisper-v3 + fish-speech")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        action = context.get("action", "stt")
        if action == "stt":
            logger.info(f"{self.name} performing Speech-to-Text")
            yield f"data: {self.name} transcribing audio using Whisper (local)...\n\n"
            # Logic for local whisper execution
        elif action == "tts":
            logger.info(f"{self.name} performing Text-to-Speech")
            yield f"data: {self.name} generating speech using Fish TTS (local)...\n\n"
            # Logic for local fish-speech execution
        
        yield f"data: {self.name} voice action completed.\n\n"
