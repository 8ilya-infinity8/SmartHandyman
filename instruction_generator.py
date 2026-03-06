"""Generates repair instructions using RAG and LLM."""

from llm_client import LLMClient
from config import TEXT_MODEL
import requests
from bs4 import BeautifulSoup


class InstructionGenerator:
    """Generates step-by-step repair instructions."""

    def __init__(self):
        self.client = LLMClient(TEXT_MODEL, use_vision=False)

    def search_repair_info(self, diagnosis, object_name):
        """Ищет релевантные чанки через FAISS. Если недоступен — пустой результат."""
        query = f"{object_name} {diagnosis}"
        try:
            from retriever import load_retriever
            hits = load_retriever().search(query, k=5, min_score=0.0)
            return {"hits": hits, "query": query}
        except Exception as e:
            print(f"[RAG] недоступен: {e}")
            return {"hits": [], "query": query}

    def generate_instructions(self, diagnosis, analysis_result, safety_info):
        """
        Generate step-by-step repair instructions.

        Args:
            diagnosis: Refined diagnosis from diagnostic agent
            analysis_result: Initial vision analysis
            safety_info: Safety check results

        Returns:
            dict with instructions and materials
        """
        object_name = analysis_result.get("object", "устройство")
        problem = diagnosis.get("refined_diagnosis", analysis_result.get("problem"))

        # Search for relevant info via RAG
        search_results = self.search_repair_info(problem, object_name)
        hits = search_results.get("hits", [])

        rag_context = ""
        if hits:
            pieces = []
            for i, h in enumerate(hits[:4], 1):
                snippet = h.get("text", "")[:600]
                src = h.get("title") or h.get("source") or h.get("provider") or "—"
                pieces.append(f"[{i}] {src}:\n{snippet}")
            rag_context = "\n\nРелевантные материалы из базы знаний:\n" + "\n---\n".join(pieces) + "\n\nИспользуй эти материалы при составлении инструкции.\n"

        prompt = f"""Ты опытный мастер по ремонту. Составь подробную пошаговую инструкцию.

Объект: {object_name}
Проблема: {problem}
Возможные причины: {", ".join(diagnosis.get("probable_causes", []))}
{rag_context}
Создай инструкцию по ремонту в формате JSON:
{{
    "title": "Название ремонта",
    "difficulty": "легко/средне/сложно",
    "estimated_time": "примерное время в минутах",
    "steps": [
        {{
            "step_number": 1,
            "title": "Название шага",
            "description": "Подробное описание",
            "warning": "предупреждение если есть"
        }}
    ],
    "tools_needed": ["инструмент 1", "инструмент 2"],
    "materials_needed": ["материал 1", "материал 2"],
    "tips": ["совет 1", "совет 2"]
}}

Инструкция должна быть понятной для непрофессионала."""

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            if result:
                result["sources"] = hits  # реальные источники из FAISS
                return result
            else:
                # JSON parsing failed, but we have text - parse it manually
                return self._parse_text_instructions(
                    response_text, problem, search_results
                )

        except Exception as e:
            return {
                "title": "Инструкция по ремонту",
                "difficulty": "средне",
                "estimated_time": "60",
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Диагностика",
                        "description": f"Проблема: {problem}\n\nОшибка: {str(e)}",
                    }
                ],
                "tools_needed": ["Базовый набор инструментов"],
                "materials_needed": [],
                "error": str(e),
            }

    def _parse_text_instructions(self, text, problem, search_results):
        """Parse instructions from plain text when JSON parsing fails."""
        # Extract steps from text
        steps = []
        lines = text.split("\n")
        current_step = None
        step_counter = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to detect step markers
            if any(marker in line.lower() for marker in ["шаг", "step", "##"]):
                if current_step:
                    steps.append(current_step)
                current_step = {
                    "step_number": step_counter,
                    "title": line.replace("#", "").strip(),
                    "description": "",
                }
                step_counter += 1
            elif current_step:
                current_step["description"] += line + "\n"

        if current_step:
            steps.append(current_step)

        # If no steps found, use the whole text as one step
        if not steps:
            steps = [
                {
                    "step_number": 1,
                    "title": "Инструкция по ремонту",
                    "description": text,
                }
            ]

        return {
            "title": f"Ремонт: {problem}",
            "difficulty": "средне",
            "estimated_time": "60",
            "steps": steps,
            "tools_needed": ["Базовый набор инструментов"],
            "materials_needed": [],
            "sources": search_results.get("hits", []),
            "raw_text": text,
        }

    def format_instructions(self, instructions):
        """Format instructions for display."""
        output = [f"# {instructions.get('title', 'Инструкция по ремонту')}"]
        output.append(f"\n**Сложность:** {instructions.get('difficulty', 'средне')}")
        output.append(
            f"**Примерное время:** {instructions.get('estimated_time', '?')} минут"
        )

        # Tools
        tools = instructions.get("tools_needed", [])
        if tools:
            output.append("\n## 🔧 Необходимые инструменты:")
            for tool in tools:
                output.append(f"- {tool}")

        # Materials
        materials = instructions.get("materials_needed", [])
        if materials:
            output.append("\n## 🛒 Необходимые материалы:")
            for material in materials:
                output.append(f"- {material}")

        # Steps
        output.append("\n## 📋 Пошаговая инструкция:")
        for step in instructions.get("steps", []):
            output.append(
                f"\n### Шаг {step.get('step_number')}: {step.get('title', '')}"
            )
            output.append(step.get("description", ""))
            if step.get("warning"):
                output.append(f"\n⚠️ **Внимание:** {step['warning']}")

        # Tips
        tips = instructions.get("tips", [])
        if tips:
            output.append("\n## 💡 Полезные советы:")
            for tip in tips:
                output.append(f"- {tip}")

        # Sources
        sources = instructions.get("sources", [])
        if sources:
            names = [s.get("title") or s.get("source") or "—" if isinstance(s, dict) else str(s) for s in sources]
            output.append(f"\n\n*Источники: {', '.join(names)}*")

        return "\n".join(output)