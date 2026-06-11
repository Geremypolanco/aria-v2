import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class ImageAgent(BaseAgentV3):
    def __init__(self):
        super().__init__(name="ImageAgent", model="flux-1-schnell")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        logger.info(f"{self.name} generating image: {task}")
        # Call Replicate/HF for FLUX
        yield f"data: {self.name} generating image for '{task}'...\n\n"
        yield f"data: [IMAGE] https://example.com/generated.png\n\n"
