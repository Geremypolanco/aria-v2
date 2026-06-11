import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class ChatAgent(BaseAgentV3):
    def __init__(self):
        super().__init__(name="ChatAgent", model="claude-3-5-sonnet")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        logger.info(f"{self.name} executing task: {task}")
        # Call Anthropic API (Claude)
        yield f"data: {self.name} processing...\n\n"
        yield f"data: Result for {task}\n\n"
