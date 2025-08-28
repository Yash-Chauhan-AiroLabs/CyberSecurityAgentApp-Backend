# app/routes/chat.py
from fastapi import APIRouter, HTTPException
from app.db.schemas import ChatRequest, ChatResponse
from app.services.groq_service import groq_service
from app.services.executor import executor_service
from app.config.history import history_manager
from app.config.logger import logger
import json
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
        # Load history (last 5 user/assistant messages)
        history = history_manager.get(req.session_id)
        
        # Get Memory
        memory = history_manager.get_memory(req.session_id)
        logger.info(f"Memory for session {req.session_id}: {memory is not None}")

        # Classify intent
        classification = groq_service.classify_intent(history, memory, req.message)

        # Execute action based on intent
        response = executor_service.dispatch(
            intent=classification["intent"],
            file_path=classification["file_path"],
            target=classification.get("target"),
            query=req.message,
            history=history,
            memory=memory
        )

        logger.info(f"Response Type: {type(response)}")
        
        if isinstance(response, dict) and (classification["intent"] == "analyze" or classification["intent"] == "report"):
            
            # Save user message into history
            logger.info(f'History update for analyze: {req.session_id}')
            history_manager.add(req.session_id, "user", req.message)
            
            # count findings based on severity from response
            assistant_message = f"""
            {classification['intent'].capitalize()} complete. Found {len(response['result'].get('findings', []))} issues:
            high: {sum(1 for f in response['result'].get('findings', []) if f['severity'].lower() == 'high')} ,
            medium: {sum(1 for f in response['result'].get('findings', []) if f['severity'].lower() == 'medium')} ,
            low severity: {sum(1 for f in response['result'].get('findings', []) if f['severity'].lower() == 'low')} .
            """
            logger.info(f'Assistant message: {assistant_message}')            
            history_manager.add(req.session_id, "assistant", assistant_message)
            
            if classification["intent"] == "analyze":
                # Save analysis result into structured memory
                logger.info(f'Saving analysis result to memory for session: {req.session_id}')
                history_manager.set_last_analyze(req.session_id, response)
            
        else:
            
            # Save messages into history
            logger.info(f'History update for analyze: {req.session_id}')
            history_manager.add(req.session_id, "user", req.message)
            history_manager.add(req.session_id, "assistant", response)
        
        if isinstance(response, dict):
        
            return ChatResponse(
                message="Response generated successfully.",
                response=response,
                intent=classification["intent"],
                file_path=classification["file_path"],
                target=classification.get("target"),
            )
            
        else:
            return ChatResponse(
                message=response,
                response={},
                intent=classification["intent"],
                file_path=classification["file_path"],
                target=classification.get("target"),
            )

    except Exception as e:
        logger.exception("Error in /chat endpoint")
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
