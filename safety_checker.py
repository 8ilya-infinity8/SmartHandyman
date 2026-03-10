"""Safety checker for identifying dangerous repairs."""

from config import DANGER_KEYWORDS
from llm_client import LLMClient
from config import TEXT_MODEL


class SafetyChecker:
    """Evaluates repair safety and generates appropriate warnings."""

    def __init__(self):
        """Initializes the safety analyzer using the text LLM."""
        self.client = LLMClient(TEXT_MODEL, use_vision=False)

    def check_safety(self, analysis_result, user_answers=None):
        """Analyzes repair data and returns a JSON assessing the threat level."""
        problem_text = (
            f"{analysis_result.get('object', '')} "
            f"{analysis_result.get('problem', '')} "
            f"{analysis_result.get('category', '')}"
        ).lower()

        if user_answers:
            problem_text += " " + " ".join(user_answers.values()).lower()

        matched_keywords = [
            keyword for keyword in DANGER_KEYWORDS if keyword.lower() in problem_text
        ]
        has_danger_keyword = bool(matched_keywords)

        danger_level = analysis_result.get("danger_level", "medium")
        context_warning = ""
        if matched_keywords:
            context_warning = (
                f"\nВНИМАНИЕ: Сработали слова-триггеры опасности: {', '.join(matched_keywords)}. "
                "Тщательно проанализируй контекст! Это действительно опасная ситуация (например, напряжение 220В, утечка газа, прорыв трубы), "
                "безопасный бытовой предмет (например, кабель от зарядки) или вообще ложное срабатывание (совпадение части слова, например 'газ' в слове 'магазин')? "
                "Если угроза реальна, ставь is_dangerous: true."
            )

        prompt = f"""Проанализируй безопасность ремонта:

Объект: {analysis_result.get("object", "неизвестно")}
Проблема: {analysis_result.get("problem", "неизвестно")}
Категория: {analysis_result.get("category", "неизвестно")}
Уровень опасности по фото: {danger_level}{context_warning}

Определи:
1. Связан ли ремонт с реальной опасностью (ток, газ, вода, высота, токсичная химия/пыль)
2. Какие меры безопасности соблюдать (обязательно укажи СИЗ: очки, перчатки, респиратор)
3. Нужно ли вызывать специалиста

Ответь в формате JSON:
{{
    "is_dangerous": true/false,
    "danger_type": "electricity/gas/water/height/chemical/other/none",
    "safety_warnings": ["предупреждение 1", "предупреждение 2"],
    "requires_professional": true/false,
    "professional_reason": "причина почему нужен специалист"
}}"""

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            if result:
                if danger_level == "high" and not result.get("is_dangerous"):
                    result["is_dangerous"] = True
                    result["requires_professional"] = True
                    result["professional_reason"] = "Визуальный анализ выявил критическую угрозу."
                    
                    if "safety_warnings" not in result:
                        result["safety_warnings"] = []
                    result["safety_warnings"].insert(0, "🚨 Система визуального контроля заблокировала статус 'Безопасно'. Выявлен высокий риск!")
                
                return result
            else:
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
        elif danger_type == "chemical":
            messages.append(
                "\n🧪 ХИМИЯ/ПЫЛЬ: Обеспечьте проветривание! Обязательно используйте СИЗ (респиратор, очки, перчатки)!"
            )

        for warning in safety_result.get("safety_warnings", []):
            messages.append(f"\n• {warning}")

        if safety_result.get("requires_professional"):
            reason = safety_result.get(
                "professional_reason", "высокая сложность или опасность"
            )
            messages.append(f"\n\n❌ РЕКОМЕНДУЕТСЯ ВЫЗВАТЬ СПЕЦИАЛИСТА: {reason}")

        return "\n".join(messages)