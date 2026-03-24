from typing import Dict, Any, List

from .base import BaseNodeProcessor
from infra.ai.openai_client import OpenAIClient
from config.settings import settings
from errors import ProcessingError

class GenerativeAIProcessor(BaseNodeProcessor):
    """Processor for generative AI operations using OpenAI"""

    def __init__(self):
        self.openai_client = None

    async def process(self, input_data: str, config: Dict[str, Any]) -> str:
        """Process AI generation with input text"""
        try:
            if not settings.OPENAI_API_KEY:
                raise ProcessingError("AI service is not configured")

            if not self.openai_client:
                self.openai_client = OpenAIClient(settings.OPENAI_API_KEY)

            prompt = self._build_prompt(input_data, config)
            response = await self.openai_client.generate_completion(
                prompt=prompt,
                model=config.get("model", "gpt-3.5-turbo"),
                max_tokens=config.get("max_tokens", 1000),
                temperature=config.get("temperature", 0.7)
            )

            return response

        except ProcessingError:
            raise
        except Exception as exc:
            raise ProcessingError("AI generation failed") from exc

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate node configuration"""
        if "prompt" not in config:
            raise ValueError("prompt is required in configuration")

        if not isinstance(config["prompt"], str):
            raise ValueError("prompt must be a string")

        if not config["prompt"].strip():
            raise ValueError("prompt cannot be empty")

    def get_required_config_keys(self) -> List[str]:
        """Return list of required configuration keys"""
        return ["prompt"]

    def _build_prompt(self, input_data: str, config: Dict[str, Any]) -> str:
        """Build the prompt by combining template with input data"""
        prompt_template = config.get("prompt", "")

        # Replace {{input}} placeholder with actual input text
        if "{{input}}" in prompt_template:
            prompt_template = prompt_template.replace("{{input}}", input_data)

        return prompt_template
