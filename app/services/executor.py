from app.services.groq_service import groq_service
from app.config.logger import logger

class Executor:
    def dispatch(self, intent: str, file_path: str | None, target: dict | None, query: str, history: list[str]) -> str:
        logger.info(f"Executor dispatching intent={intent}, file_path={file_path}, target={target}")

        if intent == "analyze":
            return groq_service.analyze_file(file_path)

        elif intent == "fix_all":
            return groq_service.fix_file(file_path, target=None)

        elif intent == "fix_partial":
            return groq_service.fix_file(file_path, target=target)

        elif intent == "general":
            return groq_service.answer_general(history, query, file_path)

        else:
            return "I'm not sure how to handle that request."

# Global instance
executor_service = Executor()
