"""Vision LLM analyzer for identifying problems from images."""

from llm_client import LLMClient
from config import VISION_MODEL
import json


class VisionAnalyzer:
    """Analyzes images to identify objects and problems."""

    def __init__(self):
        self.client = LLMClient(VISION_MODEL, use_vision=True)

    def analyze_image(self, image_bytes):
        """
        Analyze uploaded image to identify the problem.

        Args:
            image_bytes: Image file in bytes

        Returns:
            dict with analysis results
        """
        try:
            prompt = """Проанализируй это изображение поломки или неисправности.
            
Определи:
1. Что за объект/устройство (модель, если видна)
2. В чем проблема (код ошибки, видимые повреждения, протечки и т.д.)
3. Насколько это опасно (связано ли с электричеством, газом, водой)
4. Категория проблемы (сантехника, электрика, бытовая техника, строительство)

Ответь в формате JSON:
{
    "object": "название объекта/устройства",
    "brand": "бренд/модель если видна",
    "problem": "описание проблемы",
    "danger_level": "low/medium/high",
    "category": "категория",
    "visible_details": ["список видимых деталей"],
    "confidence": "уровень уверенности 0-100"
}"""

            response_text = self.client.generate_content(prompt, image=image_bytes)
            result = self.client.parse_json_response(response_text)

            if result is None:
                # Fallback: create structured response from text
                result = {
                    "object": "Не удалось определить",
                    "problem": response_text,
                    "danger_level": "medium",
                    "category": "general",
                    "confidence": 50,
                }

            return result

        except Exception as e:
            return {
                "error": str(e),
                "object": "Ошибка анализа",
                "problem": f"Не удалось проанализировать изображение: {str(e)}",
            }

    def get_initial_questions(self, analysis_result):
        """Generate initial diagnostic questions based on image analysis."""
        prompt = f"""На основе анализа изображения:
Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}

Составь 3-5 уточняющих вопросов для более точной диагностики.
Вопросы должны помочь определить причину поломки.

Верни список вопросов в формате JSON:
{{"questions": ["вопрос 1", "вопрос 2", ...]}}"""

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            if result:
                return result.get("questions", [])
            else:
                return [
                    "Когда началась проблема?",
                    "Были ли необычные звуки или запахи?",
                    "Проводилось ли обслуживание недавно?",
                ]
        except:
            return [
                "Когда началась проблема?",
                "Были ли необычные звуки или запахи?",
                "Проводилось ли обслуживание недавно?",
            ]
