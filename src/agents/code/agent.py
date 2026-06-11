import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3
from src.sandbox.executor import sandbox

logger = logging.getLogger(__name__)

class CodeAgent(BaseAgentV3):
    def __init__(self):
        super().__init__(name="CodeAgent", model="sandbox-executor")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        code = context.get("code", "")
        logger.info(f"{self.name} executing code task: {task}")
        yield f"data: {self.name} running code in isolated sandbox...\n\n"
        
        result = sandbox.execute_python(code)
        
        yield f"data: Execution Result: {result}\n\n"
        yield f"data: Code task completed.\n\n"
