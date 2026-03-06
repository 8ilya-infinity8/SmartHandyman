"""Interactive diagnostic agent that asks clarifying questions."""

from llm_client import LLMClient
from config import TEXT_MODEL, DIAGNOSTIC_TEMPERATURE, DIAGNOSTIC_MAX_TOKENS


class DiagnosticAgent:
    """
    Interactive agent for detailed problem diagnosis.

    Uses medium-low temperature for logical, focused questioning.
    """

    def __init__(self):
        # Initialize with diagnostic-specific parameters for logical reasoning
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
        # Build context from analysis
        context = f"""ПЕРВИЧНЫЙ АНАЛИЗ:
Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}
Категория: {analysis_result.get("category", "неизвестно")}
Уровень опасности: {analysis_result.get("danger_level", "неизвестно")}"""

        if previous_answers:
            context += "\n\nУЖЕ ИЗВЕСТНО (ответы пользователя):"
            for q, a in previous_answers.items():
                context += f"\n• {q}\n  → {a}"

        prompt = f"""{context}

Ты - опытный мастер-диагност с 20-летним стажем. Твоя задача - задать ЦЕЛЕВЫЕ вопросы для точной диагностики.

ПРИНЦИПЫ ДИАГНОСТИКИ:
1. Каждый вопрос должен исключать или подтверждать конкретные причины
2. Вопросы должны быть понятны обычному человеку (без технического жаргона)
3. Избегай вопросов, на которые уже есть ответы
4. Фокусируйся на симптомах, которые помогут различить похожие проблемы

ТИПЫ ПОЛЕЗНЫХ ВОПРОСОВ:
- Временные: "Когда началось?", "Как часто происходит?"
- Условные: "При каких условиях проявляется?"
- Сенсорные: "Какие звуки/запахи/ощущения?"
- Исторические: "Что делали перед поломкой?", "Были ли изменения?"

ЗАДАЧА: Составь 3-5 конкретных вопросов, которые максимально сузят круг возможных причин.

ФОРМАТ ОТВЕТА (строго JSON):
{{"questions": ["вопрос 1", "вопрос 2", "вопрос 3"]}}"""

        fallback_questions = [
            "Когда впервые появилась эта проблема?",
            "Есть ли необычные звуки, запахи или вибрация?",
            "Проводился ли ремонт или обслуживание недавно?",
        ]

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            return result.get("questions", fallback_questions) if result else fallback_questions

        except Exception as e:
            print(f"[DiagnosticAgent Generate Error]: {e}")
            return fallback_questions

    def analyze_answers(self, analysis_result, qa_pairs):
        """
        Analyze user answers to refine diagnosis.

        Synthesizes visual analysis with user responses for accurate diagnosis.

        Args:
            analysis_result: Initial vision analysis
            qa_pairs: Dict of question-answer pairs

        Returns:
            dict with refined diagnosis, probable causes, and confidence level
        """
        # Build comprehensive context
        context = f"""ВИЗУАЛЬНЫЙ АНАЛИЗ:
Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}
Категория: {analysis_result.get("category", "неизвестно")}
Видимые детали: {", ".join(analysis_result.get("visible_details", []))}

ИНФОРМАЦИЯ ОТ ПОЛЬЗОВАТЕЛЯ:"""

        for q, a in qa_pairs.items():
            context += f"\n• {q}\n  → {a}"

        prompt = f"""{context}

Ты - эксперт-диагност. Проанализируй всю информацию и сделай ТОЧНЫЙ диагноз.

МЕТОДОЛОГИЯ АНАЛИЗА:
1. Сопоставь визуальные признаки с ответами пользователя
2. Исключи маловероятные причины на основе противоречий
3. Определи наиболее вероятные причины по совпадению симптомов
4. Оцени уверенность: 90-100% = очевидно, 70-89% = вероятно, 50-69% = возможно, <50% = неясно

ЗАДАЧА: Сформулируй уточненный диагноз с конкретными причинами.

ФОРМАТ ОТВЕТА (строго JSON):
{{
    "refined_diagnosis": "точный диагноз с указанием конкретной неисправности",
    "probable_causes": [
        "наиболее вероятная причина (с объяснением)",
        "альтернативная причина (если есть)"
    ],
    "confidence": 85,
    "additional_info": "важная информация для ремонта или предупреждения"
}}

ВАЖНО: Будь конкретным. Вместо "проблема с водой" напиши "засор фильтра сливного насоса"."""

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
            print(f"[DiagnosticAgent Analyze Error]: {e}")
            fallback_diagnosis["error"] = str(e)
            return fallback_diagnosis
