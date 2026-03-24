import aiohttp

from config.logging import get_logger
from errors import ProcessingError

class OpenAIClient:
    """OpenAI API client for generative AI requests"""

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.logger = get_logger("infra.openai")

    async def generate_completion(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate text completion using OpenAI Chat API"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(
                            "OpenAI API request failed with status=%s body=%s",
                            response.status,
                            error_text,
                        )
                        raise ProcessingError("AI service request failed")

                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
        except ProcessingError:
            raise
        except aiohttp.ClientError as exc:
            self.logger.exception("Network error while calling OpenAI API")
            raise ProcessingError("AI service request failed") from exc
        except Exception as exc:
            self.logger.exception("Unexpected error while calling OpenAI API")
            raise ProcessingError("AI service request failed") from exc
