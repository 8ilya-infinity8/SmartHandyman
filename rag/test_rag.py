import json

import sys
from pathlib import Path

# Добавляем корень проекта (/app/rag) в sys.path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()  # если test_rag.py в rag/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from instruction_generator import InstructionGenerator
from rag.retriever import load_retriever


def test_retriever():
    print("=== ТЕСТ ПОИСКА RAG (только индекс) ===")
    retriever = load_retriever()
    query = "посудомойка не включается"
    hits = retriever.search(query, k=5, min_score=0.3)
    print(f"Запрос: {query}")
    print(f"Найдено чанков: {len(hits)}")
    for i, h in enumerate(hits, 1):
        print(f"\n[{i}] score={h['score']}")
        print("title:", h.get("title") or h.get("source") or "—")
        print("text:", (h.get("text") or "")[:200], "...")


def test_instructions():
    print("\n\n=== ТЕСТ ИНСТРУКЦИЙ С RAG ===")
    gen = InstructionGenerator()

    # Эмулируем результат анализа картинки разбитого телефона
    analysis_result = {
        "object": "смартфон с разбитым экраном",
        "problem": "видимые трещины на дисплее, частично не работает тачскрин",
        "category": "бытовая_техника",
    }

    # Эмулируем диагноз (как будто DiagnosticAgent уже отработал)
    diagnosis = {
        "refined_diagnosis": "трещины дисплея, требуется замена экрана",
        "probable_causes": [
            "удар о твёрдую поверхность",
            "падение устройства с высоты",
        ],
        "confidence": 85,
    }

    # Безопасность нам здесь не важна, можно передать пустое
    safety_info = {}

    instructions = gen.generate_instructions(diagnosis, analysis_result, safety_info)

    print("\n--- КРАТКИЙ РЕЗУЛЬТАТ ---")
    print("title:", instructions.get("title"))
    print("difficulty:", instructions.get("difficulty"))
    print("estimated_time:", instructions.get("estimated_time"))
    print("steps_count:", len(instructions.get("steps", [])))

    sources = instructions.get("sources", [])
    print("RAG источников:", len(sources))
    if sources:
        print("Названия источников:")
        for s in sources:
            print("-", s.get("title") or s.get("source") or "—")

    print("\n--- RAW JSON ---")
    print(json.dumps(instructions, ensure_ascii=False, indent=2)[:4000])


if __name__ == "__main__":
    test_retriever()
    # test_instructions()
