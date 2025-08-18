from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from app.config.settings import settings
from app.config.logger import logger


class PromptLoader:
    def __init__(self, base_dir: str = None):
        base_path = base_dir or settings.PROMPT_LIBRARY_PATH
        self.base_path = Path(base_path).resolve()

        if not self.base_path.exists():
            logger.error(f"Prompt directory not found: {self.base_path}")
            raise FileNotFoundError(f"Prompt directory not found: {self.base_path}")

        logger.info(f"Prompt directory set to: {self.base_path}")
        self.env = Environment(loader=FileSystemLoader(str(self.base_path)))

    def render(self, template_name: str, **kwargs) -> str:
        """
        Render a Jinja2 prompt template with variables.
        """
        template = self.env.get_template(template_name)
        return template.render(**kwargs)
    
# Global Instance
prompt_loader = PromptLoader(settings.PROMPT_LIBRARY_PATH)
