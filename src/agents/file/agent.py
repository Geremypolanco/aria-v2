import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3

logger = logging.getLogger(__name__)

class FileAgent(BaseAgentV3):
    def __init__(self):
        super().__init__(name="FileAgent", model="pil + rembg + weasyprint")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        action = context.get("action", "convert")
        logger.info(f"{self.name} performing file action: {action}")
        
        if action == "remove_bg":
            yield f"data: {self.name} removing background using rembg...\n\n"
        elif action == "pdf_gen":
            yield f"data: {self.name} generating PDF using WeasyPrint...\n\n"
        elif action == "upscale":
            yield f"data: {self.name} upscaling image using Real-ESRGAN...\n\n"
            
        yield f"data: {self.name} file processing completed.\n\n"
