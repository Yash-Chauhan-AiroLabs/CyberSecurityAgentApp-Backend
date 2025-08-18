# app/core/history.py
from collections import defaultdict

class HistoryManager:
    def __init__(self, max_length: int = 20):
        self.histories = defaultdict(list)
        self.max_length = max_length

    def add(self, session_id: str, role: str, message: str):
        self.histories[session_id].append({"role": role, "message": message})
        if len(self.histories[session_id]) > self.max_length:
            self.histories[session_id] = self.histories[session_id][-self.max_length:]

    def get(self, session_id: str, n: int = 5):
        return [h["message"] for h in self.histories[session_id][-n:]]

    def clear(self, session_id: str):
        self.histories[session_id] = []
        
# Global Instance
history_manager = HistoryManager()
