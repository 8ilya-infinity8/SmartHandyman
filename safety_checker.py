"""Safety checker for identifying dangerous repairs."""

from config import DANGER_KEYWORDS
from llm_client import LLMClient
from config import TEXT_MODEL


class SafetyChecker:
    """Checks if repair involves dangerous elements and provides safety warnings."""

    def __init__(self):
        self.client = LLMClient(TEXT_MODEL, use_vision=False)

    def check_safety(self, analysis_result, user_answers=None):
        """
        Check if the repair is dangerous and generate appropriate warnings.

        Args:
            analysis_result: Result from vision analysis
            user_answers: Optional user answers to diagnostic questions

        Returns:
            dict with safety information
        """
        # Quick keyword check
        problem_text = (
            f"{analysis_result.get('object', '')} "
            f"{analysis_result.get('problem', '')} "
            f"{analysis_result.get('category', '')}"
        ).lower()

        if user_answers:
            problem_text += " " + " ".join(user_answers.values()).lower()

        has_danger_keyword = any(
            keyword.lower() in problem_text for keyword in DANGER_KEYWORDS
        )

        danger_level = analysis_result.get("danger_level", "medium")

        # Use LLM for detailed safety analysis
        prompt = f"""Проанализируй безопасность ремонта:

Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}
Категория: {analysis_result.get("category", "неизвестно")}
Уровень опасности: {danger_level}

Определи:
1. Связан ли ремонт с электричеством, газом или другими опасными системами
2. Какие меры безопасности необходимо соблюдать
3. Нужно ли вызывать специалиста

Ответь в формате JSON:
{{
    "is_dangerous": true/false,
    "danger_type": "electricity/gas/water/height/other/none",
    "safety_warnings": ["предупреждение 1", "предупреждение 2", ...],
    "requires_professional": true/false,
    "professional_reason": "причина почему нужен специалист"
}}"""

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            if result:
                # Override if keywords detected
                if has_danger_keyword and not result.get("is_dangerous"):
                    result["is_dangerous"] = True
                return result
            else:
                # Fallback
                return {
                    "is_dangerous": has_danger_keyword or danger_level == "high",
                    "danger_type": "unknown",
                    "safety_warnings": [
                        "⚠️ Будьте осторожны при выполнении ремонта",
                        "⚠️ Если не уверены в своих силах, обратитесь к специалисту",
                    ],
                    "requires_professional": danger_level == "high",
                }

        except Exception as e:
            # Fallback safety response
            return {
                "is_dangerous": has_danger_keyword or danger_level == "high",
                "danger_type": "unknown",
                "safety_warnings": [
                    "⚠️ Будьте осторожны при выполнении ремонта",
                    "⚠️ Если не уверены в своих силах, обратитесь к специалисту",
                ],
                "requires_professional": danger_level == "high",
                "error": str(e),
            }

    @staticmethod
    def format_safety_message(safety_result):
        """Format safety warnings for display."""
        if not safety_result.get("is_dangerous"):
            return (
                "✅ Этот ремонт относительно безопасен для самостоятельного выполнения."
            )

        messages = ["🚨 ВНИМАНИЕ! ВАЖНЫЕ МЕРЫ БЕЗОПАСНОСТИ:"]

        danger_type = safety_result.get("danger_type", "unknown")
        if danger_type == "electricity":
            messages.append(
                "\n⚡ ЭЛЕКТРИЧЕСТВО: Отключите питание на щитке перед началом работ!"
            )
        elif danger_type == "gas":
            messages.append(
                "\n🔥 ГАЗ: Перекройте газ и проветрите помещение! При запахе газа немедленно вызовите аварийную службу!"
            )
        elif danger_type == "water":
            messages.append("\n💧 ВОДА: Перекройте воду перед началом работ!")
        elif danger_type == "height":
            messages.append(
                "\n🪜 ВЫСОТА: Используйте устойчивую стремянку, не работайте в одиночку!"
            )

        for warning in safety_result.get("safety_warnings", []):
            messages.append(f"\n• {warning}")

        if safety_result.get("requires_professional"):
            reason = safety_result.get(
                "professional_reason", "высокая сложность или опасность"
            )
            messages.append(f"\n\n❌ РЕКОМЕНДУЕТСЯ ВЫЗВАТЬ СПЕЦИАЛИСТА: {reason}")

        return "\n".join(messages)
