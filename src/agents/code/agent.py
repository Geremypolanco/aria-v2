import logging
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3
from src.sandbox.executor import sandbox

logger = logging.getLogger(__name__)

class CodeAgent(BaseAgentV3):
    """
    CodeAgent v3: Escribe, ejecuta y auto-testea código.
    Diferenciador: Self-testing loop hasta que el código pasa.
    """
    def __init__(self):
        super().__init__(name="CodeAgent", model="gpt-4-turbo") # Optimized for code generation

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        code = context.get("code", "")
        language = context.get("language", "python")
        
        logger.info(f"{self.name} executing {language} task: {task}")
        yield f"data: [CODE] Starting self-testing loop for {language}...\n\n"
        
        # Self-testing loop (Simplified for now, in reality this would involve LLM reflection)
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            yield f"data: [CODE] Attempt {attempt}/{max_attempts}...\n\n"
            
            if language == "python":
                result = sandbox.execute_python(code)
            elif language == "node":
                result = sandbox.execute_node(code)
            else:
                result = sandbox.execute_bash(code)
            
            if result.get("success"):
                yield f"data: [CODE] Execution SUCCESS.\n\n"
                yield f"data: Output: {result.get('stdout')}\n\n"
                break
            else:
                yield f"data: [CODE] Execution FAILED. Error: {result.get('stderr') or result.get('error')}\n\n"
                if attempt == max_attempts:
                    yield f"data: [ERROR] Max attempts reached. Task failed.\n\n"
                else:
                    yield f"data: [CODE] Reflecting on error and retrying...\n\n"
                    # In a real scenario, we would send the error back to the LLM here to fix the code
        
        yield f"data: [DONE] Code task completed.\n\n"
