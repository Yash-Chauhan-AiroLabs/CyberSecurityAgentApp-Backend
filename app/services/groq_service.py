from groq import Groq
from app.config.settings import settings
from app.config.logger import logger
from app.services.prompt_loader import prompt_loader

import json
import re
from pathlib import Path

class GroqService:
    def __init__(self):
        
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ API KEY unavailable.")
        
        elif not settings.ROUTER_LLM_ID or not settings.WORKER_LLM_ID:
            raise ValueError("GROQ MODEL ID unavailable (Router: {}, Worker: {}).".format(
                settings.ROUTER_LLM_ID, 
                settings.WORKER_LLM_ID
            ))
        
        else: 
            self.api_key = settings.GROQ_API_KEY
            self.router_model = settings.ROUTER_LLM_ID
            self.worker_model = settings.WORKER_LLM_ID
        
        self.client = Groq(api_key=self.api_key)
        logger.info(f"GrowqService initialized Successfully.")
        logger.info(f"Using Router Model ID: {settings.ROUTER_LLM_ID}")
        logger.info(f"Using Worker Model ID: {settings.WORKER_LLM_ID}")
        
        self.prompts = prompt_loader
        logger.info(f"Prompt Loader initialized.")

    # -------------------------
    # ROUTER: classify intent
    # -------------------------
    def classify_intent(self, history: list[str], memory: dict, query: str) -> dict:
        """
        Use the router LLM to classify what the user wants.
        Returns a dict with keys:
        {
            "intent": str,
            "file_path": str | None,
            "target": {
                "raw": str | None,
                "index": int | None,
                "description": str | None,
                "lines": list[int] | None
            }
        }
        """
        # Format last 5 messages for context
        history_text = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(history[-5:])])

        # Load prompt template
        prompt = self.prompts.render(
            "classify_intent.j2",
            history=history_text,
            memory=json.dumps(memory),
            query=query
        )
        logger.info(f"Classifying intent with prompt")

        try:
            response = self.client.chat.completions.create(
                model=self.router_model,
                messages=[
                    {"role": "system", "content": "You are a strict classifier. Reply ONLY with JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_completion_tokens=1000,
            )
            
        except Exception as e:
            logger.error(f"Error during ROUTER LLM call: {e}")
            logger.error(f"Defaulting to standard parsed structure.")
            return {
                "intent": "general",
                "file_path": None,
                "target": {
                    "raw": None,
                    "index": None,
                    "description": None,
                    "lines": None
                }
            }
            
        raw_output = response.choices[0].message.content.strip()

        # Try parsing JSON
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            # If invalid JSON, try to extract first JSON object via regex
            logger.error(f"Router returned invalid JSON. Attempting regex extraction.")
            match = re.search(r"\{.*\}", raw_output, re.DOTALL)
            if match:
                logger.info(f"Extracted JSON from response: {match.group(0)}")
                parsed = json.loads(match.group(0))
            else:
                logger.error(f"Failed to parse JSON from response completely: {raw_output}")
                logger.error(f"Defaulting to standard parsed structure.")
                parsed = {
                    "intent": "general",
                    "file_path": None,
                    "target": {
                        "raw": None,
                        "index": None,
                        "description": None,
                        "lines": None
                    }
                }

        # Normalize schema (make sure all fields exist)
        parsed.setdefault("intent", "general")
        parsed.setdefault("file_path", None)
        parsed.setdefault("target", {})
        parsed["target"].setdefault("raw", None)
        parsed["target"].setdefault("index", None)
        parsed["target"].setdefault("description", None)
        parsed["target"].setdefault("lines", None)

        logger.info(f"[Router] Classified intent: {parsed}")
        return parsed
            
    # -------------------------
    # WORKER: general answer
    # -------------------------
    def answer_general(self, history: list[str], query: str, file_path: str | None = None) -> str:
        """
        Answer general questions with history + optional file context.
        """
        history_text = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(history[-5:])])

        file_code = None
        if file_path:
            try:
                path = Path(file_path)
                if path.exists():
                    file_code = path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not read file {file_path}: {e}")

        prompt = self.prompts.render(
            "general_answer.j2",
            history=history_text,
            query=query,
            code=file_code or "",
        )

        try:
            response = self.client.chat.completions.create(
                model=self.worker_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant. Use history + code to answer precisely."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_completion_tokens=1500,
            )
            answer = response.choices[0].message.content.strip()
            logger.info("[Worker-General] Answer generated successfully.")
            return answer
        except Exception as e:
            logger.exception("General answer LLM call failed")
            return "Failed to generate general answer. Please try again."

    # -------------------------
    # WORKER: analyze file
    # -------------------------
    def analyze_file(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return f"File not found: {file_path}"

        try:
            source_code = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.exception(f"Failed to read file: {file_path}")
            return f"Failed to read file: {file_path} ({e})"

        prompt = self.prompts.render("analyze_file.j2", code=source_code)

        try:
            response = self.client.chat.completions.create(
                model=self.worker_model,
                messages=[
                    {"role": "system", "content": "You are a security analyzer. Identify vulnerabilities clearly."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_completion_tokens=2000,
            )
            analysis = response.choices[0].message.content.strip()
            logger.info(f"[Worker-Analyze] Analysis completed for {file_path}")
            return json.loads(analysis)
        except Exception as e:
            logger.exception("Analyze file LLM call failed")
            return f"Failed to analyze file {file_path}. Please try again."
        
    # -------------------------
    # WORKER: fix file
    # -------------------------    
    def report_findings(self, query: str, target: dict = None, memory: dict = None) -> str:

        if not memory:
            logger.error("No analysis memory available for reporting.")
            return "No analysis memory available. Please run an analysis first."
        if "last_analyze" not in memory:
            logger.error("No 'last_analyze' key in memory for reporting.")
            return "No analysis memory available. Please run an analysis first."
        
        analysis = memory["last_analyze"]
        
        prompt = prompt_loader.render(
            "report_findings.j2",
            query=query,
            target=target or {},
            analysis=analysis
        )

        try:
            response = self.client.chat.completions.create(
                model=settings.WORKER_LLM_ID,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
            )
            report = response.choices[0].message.content.strip()
            
        except:
            logger.exception("Woker-Report: Report findings LLM call failed")
            return "Failed to generate report. Please try again."
        
        logger.info("[Worker-Report] Report generated successfully.")
        return json.loads(report)

    # -------------------------
    # WORKER: fix file
    # -------------------------
    def fix_file(self, file_path: str, target: dict = None) -> str:
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return f"File not found: {file_path}"

        try:
            source_code = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.exception(f"Failed to read file: {file_path}")
            return f"Failed to read file: {file_path} ({e})"

        # Choose correct prompt
        if target and (target.get("raw") or target.get("index") or target.get("description")):
            prompt_template = "fix_partial_file.j2"
            logger.info(f"[Worker-Fix] Performing PARTIAL fix on {file_path} with target: {target}")
        else:
            prompt_template = "fix_file.j2"
            logger.info(f"[Worker-Fix] Performing FULL fix on {file_path}")

        prompt = self.prompts.render(
            prompt_template,
            code=source_code,
            target=target or {}
        )
        logger.debug(f"[Worker-Fix] Prompt:\n{prompt}")

        try:
            response = self.client.chat.completions.create(
                model=self.worker_model,
                messages=[
                    {"role": "system", "content": "You are a code fixer. Return only corrected code."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_completion_tokens=4000,
            )
            fixed_code = response.choices[0].message.content.strip()
            
            # Clean markdown if present
            if fixed_code.startswith('```python'):
                fixed_code = fixed_code[9:]
            if fixed_code.startswith('```'):
                fixed_code = fixed_code[3:]
            if fixed_code.endswith('```'):
                fixed_code = fixed_code[:-3]
                
            fixed_code = fixed_code.strip()
        
        except Exception as e:
            logger.exception("Fix file LLM call failed")
            return f"❌ Failed to fix file {file_path}. Please try again."

        try:
            path.write_text(fixed_code, encoding="utf-8")
            logger.info(f"[Worker-Fix] File {file_path} fixed successfully.")
            return f"✅ File {file_path} fixed successfully."
        except Exception as e:
            logger.exception(f"Failed to write fixed file: {file_path}")
            return f"❌ Failed to write fixed file: {file_path} ({e})"

# Global Instance
groq_service = GroqService()