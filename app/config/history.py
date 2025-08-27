from collections import defaultdict
from typing import Any, Dict, Optional
import json


class HistoryManager:
    def __init__(self, max_length: int = 20):
        """
        In-memory chat history manager with structured memory support.
        """
        self.histories = defaultdict(list)
        self.max_length = max_length
        self.memory: dict[str, dict[str, Any]] = defaultdict(dict)

    def add(self, session_id: str, role: str, message: str):
        """
        Add a message to the chat history for a given session.
        """
        self.histories[session_id].append({"role": role, "message": message})
        if len(self.histories[session_id]) > self.max_length:
            self.histories[session_id] = self.histories[session_id][-self.max_length:]

    def get(self, session_id: str, n: int = 5):
        """
        Get the last n messages from the chat history for a given session.
        """
        return [h["message"] for h in self.histories[session_id][-n:]]

    def clear(self, session_id: str):
        """
        Clear the chat history for a given session.
        """
        self.histories[session_id] = []

    # ---------- Structured memory (artifacts) ----------
    def set_memory(self, session_id: str, key: str, value: Any) -> None:
        """
        Store any JSON-serializable object under a key for this session.
        """
        self.memory[session_id][key] = value

    def get_memory(self, session_id: str, key: Optional[str] = None) -> Any:
        """
        Get a single key or the entire memory dict for a session.
        """
        if key is None:
            return self.memory.get(session_id, {})
        return self.memory.get(session_id, {}).get(key)

    def has_memory(self, session_id: str, key: str) -> bool:
        """
        Check if a key exists in the session's memory.
        """
        return key in self.memory.get(session_id, {})

    def set_last_analyze(self, session_id: str, payload: Dict[str, Any]) -> None:
        """
        Store the last analysis result for the session.
        """
        self.set_memory(session_id, "last_analyze", payload)

    def get_last_analyze(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the last analysis result for the session.
        """
        return self.get_memory(session_id, "last_analyze")


# Global Instance
history_manager = HistoryManager()