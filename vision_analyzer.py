import logging
from llm_client import LLMClient
from config import VISION_MODEL, VISION_TEMPERATURE, VISION_MAX_TOKENS

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """
    Analyzes images to identify objects and problems using Vision LLM.

    Uses low temperature for precise, factual identification.
    """

    def __init__(self):
        self.client = LLMClient(
            VISION_MODEL,
            use_vision=True,
            temperature=VISION_TEMPERATURE,
            max_tokens=VISION_MAX_TOKENS,
        )

    def analyze_image(self, image_bytes):
        """
        Analyze uploaded image to identify the problem.

        Uses structured prompt for consistent, detailed analysis.

        Args:
            image_bytes: Image file in bytes

        Returns:
            dict with analysis results including object, problem, danger level
        """
        if not image_bytes:
            logger.error("analyze_image called with empty image_bytes")
            return {
                "error": "Изображение не предоставлено",
                "object": "Ошибка анализа",
                "problem": "Не получено изображение для анализа. Попробуйте загрузить фото ещё раз.",
            }

        try:
            prompt = """Проанализируй изображение поломки или неисправности. Опирайся только на факты, видимые на фото.

Определи уровень опасности:
- high: электричество (провода, розетки, щитки) или газ (трубы, котлы, утечки)
- medium: вода под давлением
- low: механические повреждения без опасности

Ответь строго в формате JSON:
{
    "object": "точное название объекта/устройства",
    "brand": "бренд и модель (или 'не определен')",
    "problem": "детальное описание видимой проблемы",
    "danger_level": "low/medium/high",
    "category": "сантехника/электрика/бытовая_техника/строительство/отопление/другое",
    "visible_details": ["конкретная деталь 1", "конкретная деталь 2", "конкретная деталь 3"],
    "confidence": <число 0-100, насколько уверен в диагнозе>
}

ВАЖНО: Будь максимально конкретным. Если видишь код ошибки - укажи его точно. Если видишь модель - укажи её."""

            response_text = self.client.generate_content(prompt, image=image_bytes)
            result = self.client.parse_json_response(response_text)

            if result is None:
                result = {
                    "object": "Не удалось определить",
                    "problem": response_text,
                    "danger_level": "medium",
                    "category": "general",
                    "confidence": 50,
                }

            return result

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {
                "error": str(e),
                "object": "Ошибка анализа",
                "problem": f"Не удалось проанализировать изображение: {str(e)}",
            }
