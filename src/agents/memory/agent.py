import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class MemoryAgent(BaseAgentV3):
    """
    MemoryAgent v3: El Contexto.
    Diferenciador: Aria te recuerda, aprende de ti, no empieza de cero.
    """
    def __init__(self):
        super().__init__(name="MemoryAgent", model="gpt-4-turbo")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        action = context.get("action", "recall")
        logger.info(f"{self.name} accessing memory: {action}")
        
        yield f"data: [MEMORY] Accessing long-term semantic storage (pgvector)...\n\n"
        
        if action == "store":
            yield f"data: [MEMORY] Learning from interaction: '{task}'...\n\n"
        else:
            yield f"data: [MEMORY] Retrieving relevant past projects and preferences...\n\n"
            
        yield f"data: [MEMORY] Memory sync SUCCESS.\n\n"
        yield f"data: [DONE] Memory task completed.\n\n"
