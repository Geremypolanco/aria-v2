import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3
from src.sandbox.executor import sandbox

logger = logging.getLogger(__name__)

class FileAgent(BaseAgentV3):
    """
    FileAgent v3: El Gestor.
    Diferenciador: Entrega archivos reales, no solo texto.
    """
    def __init__(self):
        super().__init__(name="FileAgent", model="gpt-4-turbo")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        file_action = context.get("action", "create")
        filename = context.get("filename", "output.txt")
        content = context.get("content", "")
        
        logger.info(f"{self.name} performing file action: {file_action} on {filename}")
        yield f"data: [FILE] Executing {file_action} for {filename}...\n\n"
        
        if file_action == "create":
            script = f"echo '{content}' > {filename}"
            result = sandbox.execute_bash(script)
        elif file_action == "zip":
            script = f"zip -r {filename}.zip ."
            result = sandbox.execute_bash(script)
        else:
            result = sandbox.execute_bash(f"ls -lh {filename}")
            
        if result.get("success"):
            yield f"data: [FILE] File operation completed.\n\n"
            yield f"data: [FILE] Delivering real file: {filename}\n\n"
        else:
            yield f"data: [ERROR] File operation failed: {result.get('error')}\n\n"
            
        yield f"data: [DONE] File task completed.\n\n"
