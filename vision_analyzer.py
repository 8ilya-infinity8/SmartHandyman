"""Vision LLM analyzer for identifying problems from images."""

from llm_client import LLMClient
from config import VISION_MODEL, VISION_TEMPERATURE, VISION_MAX_TOKENS
import json


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
        try:
            prompt = """Ты - эксперт по диагностике бытовых устройств и систем. Внимательно изучи изображение.

ЗАДАЧА: Проанализируй изображение поломки или неисправности максимально детально.
ОПИРАЙСЯ ТОЛЬКО НА ФАКТЫ, видимые на фото. Не придумывай детали, которых не видно.

АНАЛИЗИРУЙ:
1. ОБЪЕКТ/УСТРОЙСТВО:
   - Тип устройства (стиральная машина, кран, розетка и т.д.)
   - Бренд и модель (если видны логотипы, маркировки)
   - Материал и конструкция

2. ПРОБЛЕМА:
   - Видимые повреждения (трещины, коррозия, протечки)
   - Коды ошибок на дисплее (если есть)
   - Неправильное положение деталей
   - Следы износа или неисправности

3. ОПАСНОСТЬ:
   - Связано ли с электричеством (провода, розетки, щитки) → high
   - Связано ли с газом (трубы, котлы, утечки) → high
   - Связано ли с водой под давлением → medium
   - Механические повреждения без опасности → low

4. КОНТЕКСТ:
   - Где находится (кухня, ванная, подвал, улица)
   - Видимые детали окружения
   - Признаки недавнего использования

ФОРМАТ ОТВЕТА (строго JSON):
{
    "object": "точное название объекта",
    "brand": "бренд и модель (или 'не определен')",
    "problem": "детальное описание проблемы",
    "danger_level": "low/medium/high",
    "category": "сантехника/электрика/бытовая_техника/строительство/отопление",
    "visible_details": ["деталь 1", "деталь 2", "деталь 3"],
    "confidence": 85
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
            print(f"[VisionAnalyzer Error]: {e}")
            return {
                "error": str(e),
                "object": "Ошибка анализа",
                "problem": f"Не удалось проанализировать изображение: {str(e)}",
            }
