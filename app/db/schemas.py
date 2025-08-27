from pydantic import BaseModel
from typing import Any, Dict

# ---------- Request/Response Models ----------
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    message: str
    response: Dict[str, Any]
    intent: str
    file_path: str | None = None
    target: dict | None = None

