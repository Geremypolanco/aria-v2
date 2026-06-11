import logging
import os
from typing import Any, Dict, AsyncGenerator
from src.agents.base_v3 import BaseAgentV3
from src.sandbox.executor import sandbox

logger = logging.getLogger(__name__)

class GitAgent(BaseAgentV3):
    """
    GitAgent v3: El Ingeniero de Repos.
    Diferenciador: Opera directamente sobre GitHub via API y git CLI.
    """
    def __init__(self):
        super().__init__(name="GitAgent", model="gpt-4-turbo")

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        action = context.get("action", "status")
        repo_url = context.get("repo_url", "")
        commit_msg = context.get("commit_message", "feat: update by ARIA")
        
        logger.info(f"{self.name} performing git action: {action}")
        yield f"data: [GIT] Initiating {action} on {repo_url or 'local'}...\n\n"
        
        if action == "clone":
            script = f"git clone {repo_url} ."
            result = sandbox.execute_bash(script)
        elif action == "push":
            script = f"git add . && git commit -m '{commit_msg}' && git push origin main"
            result = sandbox.execute_bash(script)
        else:
            result = sandbox.execute_bash("git status")
            
        if result.get("success"):
            yield f"data: [GIT] Action {action} completed successfully.\n\n"
            yield f"data: {result.get('stdout')}\n\n"
        else:
            yield f"data: [ERROR] Git action failed: {result.get('stderr') or result.get('error')}\n\n"
        
        yield f"data: [DONE] Git task completed.\n\n"
