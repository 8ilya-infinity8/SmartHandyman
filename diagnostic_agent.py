"""Interactive diagnostic agent that asks clarifying questions."""

from llm_client import LLMClient
from config import TEXT_MODEL


class DiagnosticAgent:
    """Interactive agent for detailed problem diagnosis."""

    def __init__(self):
        self.client = LLMClient(TEXT_MODEL, use_vision=False)
        self.conversation_history = []

    def generate_questions(self, analysis_result, previous_answers=None):
        """
        Generate diagnostic questions based on analysis and previous answers.

        Args:
            analysis_result: Initial vision analysis
            previous_answers: Dict of previous Q&A pairs

        Returns:
            list of questions
        """
        context = f"""Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}
Категория: {analysis_result.get("category", "неизвестно")}"""

        if previous_answers:
            context += "\n\nПредыдущие ответы:"
            for q, a in previous_answers.items():
                context += f"\nВ: {q}\nО: {a}"

        prompt = f"""{context}

Ты опытный мастер-диагност. Задай 3-5 уточняющих вопросов, которые помогут точно определить причину поломки.
Вопросы должны быть конкретными и помогать сузить круг возможных причин.

Верни только список вопросов в формате JSON:
{{"questions": ["вопрос 1", "вопрос 2", "вопрос 3"]}}"""

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            if result:
                return result.get("questions", [])
            else:
                return [
                    "Когда впервые появилась эта проблема?",
                    "Есть ли необычные звуки, запахи или вибрация?",
                    "Проводился ли ремонт или обслуживание недавно?",
                ]

        except Exception as e:
            # Fallback questions
            return [
                "Когда впервые появилась эта проблема?",
                "Есть ли необычные звуки, запахи или вибрация?",
                "Проводился ли ремонт или обслуживание недавно?",
            ]

    def analyze_answers(self, analysis_result, qa_pairs):
        """
        Analyze user answers to refine diagnosis.

        Args:
            analysis_result: Initial vision analysis
            qa_pairs: Dict of question-answer pairs

        Returns:
            dict with refined diagnosis
        """
        context = f"""Первичный анализ:
Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}

Ответы пользователя:"""

        for q, a in qa_pairs.items():
            context += f"\nВ: {q}\nО: {a}"

        prompt = f"""{context}

На основе визуального анализа и ответов пользователя, уточни диагноз.

Верни результат в формате JSON:
{{
    "refined_diagnosis": "уточненный диагноз",
    "probable_causes": ["причина 1", "причина 2"],
    "confidence": "уровень уверенности 0-100",
    "additional_info": "дополнительная важная информация"
}}"""

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            if result:
                return result
            else:
                return {
                    "refined_diagnosis": analysis_result.get(
                        "problem", "Не определено"
                    ),
                    "probable_causes": ["Требуется дополнительная диагностика"],
                    "confidence": 50,
                }

        except Exception as e:
            return {
                "refined_diagnosis": analysis_result.get("problem", "Не определено"),
                "probable_causes": ["Требуется дополнительная диагностика"],
                "confidence": 50,
                "error": str(e),
            }

    def should_ask_more_questions(self, confidence_level, num_questions_asked):
        """Determine if more questions are needed."""
        if num_questions_asked >= 3:  # Max 3 rounds of questions
            return False
        if confidence_level >= 80:  # High confidence
            return False
        return True
