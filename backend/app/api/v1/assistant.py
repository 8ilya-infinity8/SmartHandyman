import base64
import os
import sys
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_user

# Поднимаемся до корня проекта, чтобы импортировать общие агенты.
# В Docker корень проекта смонтирован в /app, поэтому путь можно
# переопределить через переменную окружения PROJECT_ROOT.
PROJECT_ROOT = os.getenv(
    "PROJECT_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")),
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from diagnostic_agent import DiagnosticAgent  # type: ignore  # noqa: E402
from instruction_generator import InstructionGenerator  # type: ignore  # noqa: E402
from safety_checker import SafetyChecker  # type: ignore  # noqa: E402
from shopping_agent import ShoppingAgent  # type: ignore  # noqa: E402
from vision_analyzer import VisionAnalyzer  # type: ignore  # noqa: E402

router = APIRouter(prefix="/assistant", tags=["assistant"])


class QAItem(BaseModel):
    question: str
    answer: str


class RepairRequest(BaseModel):
    """Запрос от фронтенда к ассистенту-ремонтнику."""

    question: str = Field(
        ..., description="Текстовый запрос пользователя с описанием проблемы"
    )
    image_base64: Optional[str] = Field(
        None,
        description="Изображение в base64 (опционально). Если не передано, анализ идёт только по тексту.",
    )
    qa: Optional[List[QAItem]] = Field(
        None,
        description="Ответы пользователя на уточняющие вопросы (если уже были заданы ранее).",
    )


class RepairResponse(BaseModel):
    """Сводный ответ ассистента-ремонтника."""

    analysis: Dict[str, Any]
    diagnosis: Dict[str, Any]
    safety: Dict[str, Any]
    instructions: Dict[str, Any]
    shopping: Dict[str, Any]


def _decode_image(image_base64: Optional[str]) -> Optional[bytes]:
    if not image_base64:
        return None
    try:
        # поддерживаем варианты с префиксом data:image/...
        if "," in image_base64:
            _, b64 = image_base64.split(",", 1)
        else:
            b64 = image_base64
        return base64.b64decode(b64)
    except Exception as e:  # pragma: no cover - защитный код
        raise HTTPException(status_code=400, detail=f"Invalid image_base64: {e}")


@router.post("/repair", response_model=RepairResponse)
async def run_repair_assistant(
    payload: RepairRequest,
    user=Depends(get_current_user),
):
    """
    Оркестратор всех агентов:

    - VisionAnalyzer: анализ фото (если есть)
    - DiagnosticAgent: уточнение диагноза по ответам пользователя
    - SafetyChecker: проверка безопасности
    - InstructionGenerator: пошаговая инструкция по ремонту с RAG
    - ShoppingAgent: список покупок и оценка сметы

    Возвращает один JSON для фронтенда.
    """

    image_bytes = _decode_image(payload.image_base64)

    # 1. Анализ изображения (или базовый анализ только по тексту)
    if image_bytes:
        analyzer = VisionAnalyzer()
        analysis = analyzer.analyze_image(image_bytes)
    else:
        # fallback: минимальный "анализ" из текста
        analysis = {
            "object": "Неизвестный объект",
            "problem": payload.question,
            "danger_level": "medium",
            "category": "general",
            "visible_details": [],
            "confidence": 50,
        }

    # 2. Сбор ответов пользователя
    qa_pairs: Dict[str, str] = {}
    if payload.qa:
        for item in payload.qa:
            qa_pairs[item.question] = item.answer

    # 3. Диагностика
    diagnostic_agent = DiagnosticAgent()
    diagnosis = diagnostic_agent.analyze_answers(analysis, qa_pairs)

    # 4. Проверка безопасности
    safety_checker = SafetyChecker()
    safety = safety_checker.check_safety(analysis, qa_pairs)

    # 5. Генерация инструкции
    instr_generator = InstructionGenerator()
    instructions = instr_generator.generate_instructions(diagnosis, analysis, safety)

    # 6. Список покупок и смета
    shopping_agent = ShoppingAgent()
    shopping_list = shopping_agent.generate_shopping_list(instructions)
    cost_estimate = shopping_agent.estimate_total_cost(shopping_list)

    shopping = {"list": shopping_list, "cost": cost_estimate}

    return RepairResponse(
        analysis=analysis,
        diagnosis=diagnosis,
        safety=safety,
        instructions=instructions,
        shopping=shopping,
    )

