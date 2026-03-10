import logging
from llm_client import LLMClient
from config import TEXT_MODEL, DIAGNOSTIC_TEMPERATURE, DIAGNOSTIC_MAX_TOKENS

logger = logging.getLogger(__name__)


class DiagnosticAgent:
    """
    Interactive agent for detailed problem diagnosis.

    Uses medium-low temperature for logical, focused questioning.
    """

    def __init__(self):
        self.client = LLMClient(
            TEXT_MODEL,
            use_vision=False,
            temperature=DIAGNOSTIC_TEMPERATURE,
            max_tokens=DIAGNOSTIC_MAX_TOKENS,
        )

    def generate_questions(self, analysis_result, previous_answers=None):
        """
        Generate diagnostic questions based on analysis and previous answers.

        Uses logical reasoning to narrow down possible causes.

        Args:
            analysis_result: Initial vision analysis
            previous_answers: Dict of previous Q&A pairs

        Returns:
            list of targeted diagnostic questions
        """
        context = f"""Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}
Категория: {analysis_result.get("category", "неизвестно")}
Уровень опасности: {analysis_result.get("danger_level", "неизвестно")}"""

        if previous_answers:
            context += "\n\nУже известно (ответы пользователя):"
            for q, a in previous_answers.items():
                context += f"\n• {q}\n  → {a}"

        prompt = f"""{context}

Задай 3-5 вопросов для точной диагностики. Требования:
- Каждый вопрос должен исключать или подтверждать конкретную причину поломки
- Формулируй понятно для обычного человека, без технического жаргона
- Не повторяй вопросы, на которые уже есть ответы выше

Ответь строго в формате JSON:
{{"questions": ["вопрос 1", "вопрос 2", "вопрос 3"]}}"""

        fallback_questions = [
            "Когда впервые появилась эта проблема?",
            "Есть ли необычные звуки, запахи или вибрация?",
            "Проводился ли ремонт или обслуживание недавно?",
        ]

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            return (
                result.get("questions", fallback_questions)
                if result
                else fallback_questions
            )

        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            return fallback_questions

    def analyze_answers(self, analysis_result, qa_pairs):
        """
        Analyze user answers to refine diagnosis.

        Args:
            analysis_result: Initial vision analysis
            qa_pairs: Dict of question-answer pairs

        Returns:
            dict with refined diagnosis, probable causes, and confidence level
        """
        context = f"""Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}
Категория: {analysis_result.get("category", "неизвестно")}
Видимые детали: {", ".join(analysis_result.get("visible_details", []))}

Ответы пользователя:"""

        for q, a in qa_pairs.items():
            context += f"\n- {q}\n -> {a}"

        prompt = f"""{context}
На основе визуального анализа и ответов пользователя сформулируй точный диагноз.
Оцени уверенность: 90-100 = очевидно, 70-89 = вероятно, 50-69 = возможно, <50 = неясно.

Ответь строго в формате JSON:
{{
    "refined_diagnosis": "конкретная неисправность (например: 'засор фильтра сливного насоса', а не 'проблема с водой')",
    "probable_causes": [
        "наиболее вероятная причина с объяснением",
        "альтернативная причина (если есть)"
    ],
    "confidence": <число 0-100>,
    "additional_info": "важное для ремонта или безопасности"
}}
"""
        fallback_diagnosis = {
            "refined_diagnosis": analysis_result.get("problem", "Не определено"),
            "probable_causes": ["Требуется дополнительная диагностика"],
            "confidence": 50,
        }

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            return result if result else fallback_diagnosis

        except Exception as e:
            logger.error(f"Failed to analyze answers: {e}")
            fallback_diagnosis["error"] = str(e)
            return fallback_diagnosis
