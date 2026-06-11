import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class WriterAgent(BaseAgentV3):
    def __init__(self):
        super().__init__(name="WriterAgent", model="claude-3-5-sonnet (creative)")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        logger.info(f"{self.name} writing: {task}")
        yield f"data: {self.name} drafting high-conversion content for '{task}'...\n\n"
        # Specialized prompts for products/articles
        yield f"data: Content generation completed.\n\n"
