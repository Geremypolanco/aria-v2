from abc import ABC, abstractmethod
from typing import Any, Dict, AsyncGenerator

class BaseAgentV3(ABC):
    """
    Base class for all ARIA v3.0 specialized agents.
    """
    
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Execute the assigned task and yield progress/results via SSE chunks.
        """
        pass
