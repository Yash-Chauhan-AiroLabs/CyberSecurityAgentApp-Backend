# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from app.db.schemas import ChatRequest, ChatResponse
from app.services.groq_service import groq_service
from app.services.executor import executor_service
from app.config.history import history_manager
from app.config.logger import logger
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

# Router Instance
router = APIRouter()

# ---------- Route ----------
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Main chat endpoint. Handles all queries:
    - analyze
    - fix_all
    - fix_partial
    - general
    """

    try:
        # 1. Load history (last 5 user/assistant messages)
        history = history_manager.get(req.session_id)

        # 2. Classify intent
        classification = groq_service.classify_intent(history, req.message)

        # 3. Execute action based on intent
        response_text = executor_service.dispatch(
            intent=classification["intent"],
            file_path=classification["file_path"],
            target=classification.get("target"),
            query=req.message,
            history=history
        )

        # 4. Save messages into history
        history_manager.add(req.session_id, "user", req.message)
        history_manager.add(req.session_id, "assistant", response_text)

        # 5. Return response
        return ChatResponse(
            response=response_text,
            intent=classification["intent"],
            file_path=classification["file_path"],
            target=classification.get("target"),
        )

    except Exception as e:
        logger.exception("Error in /chat endpoint")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
