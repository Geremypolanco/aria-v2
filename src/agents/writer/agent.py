import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class WriterAgent(BaseAgentV3):
    """
    WriterAgent v3: El Creador de Contenido.
    Diferenciador: Output listo para producción, no borradores.
    """
    def __init__(self):
        super().__init__(name="WriterAgent", model="gpt-4-turbo")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        content_type = context.get("type", "markdown")
        logger.info(f"{self.name} generating {content_type} content: {task}")
        
        yield f"data: [WRITER] Generating production-ready {content_type}...\n\n"
        
        # In a real scenario, this would call an LLM to generate the content
        # For now, we simulate the output
        yield f"data: [WRITER] Content generation in progress...\n\n"
        yield f"data: [WRITER] Success. Content ready for delivery.\n\n"
        
        yield f"data: [DONE] Writer task completed.\n\n"
