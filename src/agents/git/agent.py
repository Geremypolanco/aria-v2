import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class GitAgent(BaseAgentV3):
    def __init__(self):
        super().__init__(name="GitAgent", model="github-api")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        logger.info(f"{self.name} managing git: {task}")
        # Use gh CLI or GitHub API
        yield f"data: {self.name} performing git action: {task}...\n\n"
        yield f"data: Git action completed.\n\n"
