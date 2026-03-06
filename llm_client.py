"""Unified LLM client supporting Claude and OpenAI."""

import base64
import json
import re
from PIL import Image
import io
from config import (
    LLM_PROVIDER,
    CLAUDE_API_KEY,
    CLAUDE_BASE_URL,
    OPENAI_API_KEY,
    SYSTEM_PROMPT,
)


class LLMClient:
    """
    Unified client for LLM operations supporting multiple providers.

    Handles both vision and text tasks with appropriate parameters.
    """

    def __init__(self, model_name, use_vision=False, temperature=None, max_tokens=None):
        """
        Initialize LLM client.

        Args:
            model_name: Name of the model to use
            use_vision: Whether this client will process images
            temperature: Sampling temperature (0.0-1.0). If None, uses defaults from config
            max_tokens: Maximum tokens to generate. If None, uses defaults from config
        """
        self.provider = LLM_PROVIDER
        self.model_name = model_name
        self.use_vision = use_vision
        self.temperature = temperature
        self.max_tokens = max_tokens

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

    def _process_image(self, image):
        """Optimizes the image size and converts into Base64 JPEG."""
        if isinstance(image, bytes):
            img = Image.open(io.BytesIO(image))
        else:
            img = image

        if img.mode != "RGB":
            img = img.convert("RGB")

        max_size = 1600
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)

        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return base64_image, "image/jpeg"

    def _generate_claude(self, prompt, image=None):
        """
        Generate content using Claude API.

        Handles image encoding and uses configured temperature/max_tokens.
        """
        messages = []

        if image:
            base64_image, mime_type = self._process_image(image)

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": base64_image,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            )
        else:
            messages.append({"role": "user", "content": prompt})

        # Use instance max_tokens or default to 4096
        max_tokens = self.max_tokens if self.max_tokens is not None else 4096

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=messages,
        )

        # Extract text from response, handling ThinkingBlock and other block types
        text_parts = []
        for block in response.content:
            if hasattr(block, "text"):
                text_parts.append(block.text)

        return "\n".join(text_parts) if text_parts else ""

    def _generate_openai(self, prompt, image=None):
        """
        Generate content using OpenAI API.

        Handles image encoding and uses configured temperature/max_tokens.
        """
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
            base64_image, mime_type = self._process_image(image)

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}",
                                "detail": "high"
                            },
                        },
                    ],
                }
            )
        else:
            messages.append({"role": "user", "content": prompt})

        # Use instance parameters or defaults
        temperature = self.temperature if self.temperature is not None else 0.7
        max_tokens = self.max_tokens if self.max_tokens is not None else 4096

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content

    def parse_json_response(self, response_text):
        """Parse JSON from LLM response with Regex."""
        if not response_text:
            return None

        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            match = re.search(r'\{.*?\}', response_text, re.DOTALL)
            json_str = match.group(0) if match else response_text

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
