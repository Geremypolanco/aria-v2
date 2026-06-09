from typing import List, Dict, Any

class Memory:
    def __init__(self):
        self._storage = []
    
    def add(self, event_type: str, content: str, metadata: Dict = None):
        self._storage.append({"type": event_type, "content": content, "metadata": metadata or {}})
        if len(self._storage) > 50: self._storage.pop(0)
    
    def get_recent(self, limit: int = 10):
        return self._storage[-limit:]

memory = Memory()