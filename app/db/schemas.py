from pydantic import BaseModel

# ---------- Request/Response Models ----------
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str
    file_path: str | None = None
    target: dict | None = None

