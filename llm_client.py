"""Unified LLM client supporting Claude and OpenAI."""

import base64
import json
from PIL import Image
import io
from config import (
    LLM_PROVIDER,
    CLAUDE_API_KEY,
    CLAUDE_BASE_URL,
    OPENAI_API_KEY,
)


class LLMClient:
    """Unified client for LLM operations supporting multiple providers."""

    def __init__(self, model_name, use_vision=False):
        self.provider = LLM_PROVIDER
        self.model_name = model_name
        self.use_vision = use_vision

        if self.provider == "claude":
            import anthropic

            self.client = anthropic.Anthropic(
                api_key=CLAUDE_API_KEY, base_url=CLAUDE_BASE_URL
            )
        elif self.provider == "openai":
            import openai

            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}. Use 'claude' or 'openai'."
            )

    def generate_content(self, prompt, image=None):
        """
        Generate content from text prompt and optional image.

        Args:
            prompt: Text prompt
            image: PIL Image or bytes (optional)

        Returns:
            Generated text response
        """
        if self.provider == "claude":
            return self._generate_claude(prompt, image)
        elif self.provider == "openai":
            return self._generate_openai(prompt, image)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _generate_claude(self, prompt, image=None):
        """Generate content using Claude."""
        messages = []

        if image:
            # Convert image to base64
            if isinstance(image, bytes):
                image_data = image
            else:
                # PIL Image
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                image_data = buffer.getvalue()

            base64_image = base64.b64encode(image_data).decode("utf-8")

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            )
        else:
            messages.append({"role": "user", "content": prompt})

        # System prompt to override default behavior
        system_prompt = """Ты - экспертная система для диагностики и ремонта бытовых устройств. 
Твоя задача - помогать пользователям с ремонтом техники, сантехники, электрики и других бытовых проблем.
Отвечай на русском языке, давай конкретные практические инструкции.
Всегда следуй формату, указанному в запросе пользователя."""

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
        )

        # Extract text from response, handling ThinkingBlock and other block types
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        return "\n".join(text_parts) if text_parts else ""

    def _generate_openai(self, prompt, image=None):
        """Generate content using OpenAI."""
        messages = [
            {
                "role": "system",
                "content": """Ты - экспертная система для диагностики и ремонта бытовых устройств. 
Твоя задача - помогать пользователям с ремонтом техники, сантехники, электрики и других бытовых проблем.
Отвечай на русском языке, давай конкретные практические инструкции.
Всегда следуй формату, указанному в запросе пользователя.""",
            }
        ]

        if image:
            # Convert image to base64
            if isinstance(image, bytes):
                image_data = image
            else:
                # PIL Image
                buffer = io.BytesIO()
                image.save(buffer, format="PNG")
                image_data = buffer.getvalue()

            base64_image = base64.b64encode(image_data).decode("utf-8")

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            )
        else:
            messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name, messages=messages, temperature=0.7, max_tokens=4096
        )

        return response.choices[0].message.content

    def parse_json_response(self, response_text):
        """Parse JSON from LLM response."""
        # Try to extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Return None if parsing fails
            return None
