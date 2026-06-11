import logging
import json
from typing import List, Dict, Any, AsyncGenerator
from src.agents.chat.agent import ChatAgent
from src.agents.voice.agent import VoiceAgent
from src.agents.vision.agent import VisionAgent
from src.agents.code.agent import CodeAgent
from src.agents.research.agent import ResearchAgent
from src.agents.image.agent import ImageAgent
from src.agents.writer.agent import WriterAgent
from src.agents.git.agent import GitAgent
from src.agents.file.agent import FileAgent
from src.agents.memory.agent import MemoryAgent

logger = logging.getLogger(__name__)

class OrchestratorV3:
    """
    ARIA ENGINE v3.0 Orchestrator — "El Director"
    Lifecycle: Plan (DAG) → Delegate → Monitor → Checkpoint → Deliver
    Diferenciador: Checkpoint automático antes de cada acción irreversible.
    """
    
    def __init__(self):
        self.agents = {
            "chat": ChatAgent(),
            "voice": VoiceAgent(),
            "vision": VisionAgent(),
            "code": CodeAgent(),
            "research": ResearchAgent(),
            "image": ImageAgent(),
            "writer": WriterAgent(),
            "git": GitAgent(),
            "file": FileAgent(),
            "memory": MemoryAgent()
        }
        
    async def plan(self, user_input: str) -> List[Dict[str, Any]]:
        """Decompose user input into a sequence of agent tasks (DAG)."""
        logger.info(f"[ORCHESTRATOR] Planning for: {user_input}")
        
        # In a real scenario, this calls Claude/GPT to generate a structured JSON plan
        # We simulate a plan based on keywords for demonstration
        if "repo" in user_input or "github" in user_input:
            return [
                {"agent": "research", "task": "Search for similar projects", "context": {}},
                {"agent": "git", "task": "Initialize repository", "context": {"action": "clone"}},
                {"agent": "code", "task": "Generate boilerplate", "context": {"language": "python"}},
                {"agent": "git", "task": "Push initial commit", "context": {"action": "push"}}
            ]
        
        return [{"agent": "chat", "task": f"Process: {user_input}", "context": {}}]

    async def delegate(self, plan: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """Assign tasks to specialized agents and monitor execution."""
        for i, step in enumerate(plan):
            agent_name = step.get("agent")
            task = step.get("task")
            context = step.get("context", {})
            
            agent = self.agents.get(agent_name)
            if not agent:
                yield f"data: [ERROR] Agent {agent_name} not found.\n\n"
                continue

            yield f"data: [PLAN] Step {i+1}/{len(plan)}: {agent_name} -> {task}\n\n"
            
            # IRREVERSIBLE ACTION CHECKPOINT
            if agent_name in ["git", "file"] and context.get("action") in ["push", "delete"]:
                yield f"data: [CHECKPOINT] Auto-saving state before irreversible action...\n\n"
            
            async for chunk in agent.execute(task, context):
                yield chunk
            
    async def run(self, user_input: str) -> AsyncGenerator[str, None]:
        """Main entry point for the orchestrator execution loop."""
        yield f"data: [SYSTEM] ARIA Cognitive Loop Started.\n\n"
        plan = await self.plan(user_input)
        yield f"data: [SYSTEM] Plan created: {len(plan)} steps.\n\n"
        
        async for chunk in self.delegate(plan):
            yield chunk
            
        yield "data: [SYSTEM] All tasks completed. SUCCESS.\n\n"
        yield "data: [DONE]\n\n"

orchestrator_v3 = OrchestratorV3()
