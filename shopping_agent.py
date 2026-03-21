"""Shopping list generator and price estimator."""

import json
import logging
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from ddgs import DDGS

from config import TEXT_MODEL
from llm_client import LLMClient

logger = logging.getLogger(__name__)

STORE_NAMES = {
    "ozon.ru": "Ozon",
    "wildberries.ru": "Wildberries",
    "market.yandex.ru": "Яндекс Маркет",
    "leroymerlin.ru": "Леруа Мерлен",
    "lemanapro.ru": "Лемана ПРО",
    "vseinstrumenti.ru": "ВсеИнструменты",
    "dns-shop.ru": "DNS",
    "mvideo.ru": "М.Видео",
    "citilink.ru": "Ситилинк",
    "petrovich.ru": "Петрович",
    "maxidom.ru": "Максидом",
    "sbermegamarket.ru": "МегаМаркет",
    "megamarket.ru": "МегаМаркет",
    "chipdip.ru": "ChipDip",
    "220-volt.ru": "220 Вольт",
    "kuvalda.ru": "Кувалда.ру",
    "stroylandiya.ru": "Стройландия",
}


def _domain_to_store(url: str) -> str:
    try:
        host = urlparse(url).netloc.replace("www.", "")
        if host in STORE_NAMES:
            return STORE_NAMES[host]
        for domain, name in STORE_NAMES.items():
            if domain in host:
                return name
        return host.split(".")[0].capitalize()
    except Exception:
        return "Интернет-магазин"


def _extract_json_objects(text: str) -> List[Dict]:
    """Robustly extract a list of JSON objects from LLM output."""
    stripped = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.MULTILINE)
    stripped = re.sub(r"\n?```$", "", stripped, flags=re.MULTILINE).strip()

    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return [x for x in parsed if isinstance(x, dict)]
    except json.JSONDecodeError:
        pass

    start, end = stripped.find("["), stripped.rfind("]")
    if start != -1 and end > start:
        try:
            parsed = json.loads(stripped[start : end + 1])
            if isinstance(parsed, list):
                return [x for x in parsed if isinstance(x, dict)]
        except json.JSONDecodeError:
            pass

    objects, pos = [], 0
    while pos < len(stripped):
        obj_start = stripped.find("{", pos)
        if obj_start == -1:
            break
        depth, in_string, escape, obj_end = 0, False, False, -1
        for i in range(obj_start, len(stripped)):
            ch = stripped[i]
            if escape:
                escape = False
                continue
            if ch == "\\" and in_string:
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    obj_end = i
                    break
        if obj_end == -1:
            try:
                obj = json.loads(stripped[obj_start:] + "}")
                if isinstance(obj, dict) and "name" in obj:
                    objects.append(obj)
            except json.JSONDecodeError:
                pass
            break
        try:
            obj = json.loads(stripped[obj_start : obj_end + 1])
            if isinstance(obj, dict):
                objects.append(obj)
        except json.JSONDecodeError:
            pass
        pos = obj_end + 1

    return objects


def _parse_dict_response(text: str) -> Optional[Dict]:
    """Extract the outermost JSON object from LLM response text."""
    stripped = re.sub(r"^```[a-z]*\n?", "", text.strip(), flags=re.MULTILINE)
    stripped = re.sub(r"\n?```$", "", stripped, flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    start, end = stripped.find("{"), stripped.rfind("}")
    if start != -1 and end > start:
        try:
            parsed = json.loads(stripped[start : end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return None


class ShoppingAgent:
    def __init__(self):
        self.client = LLMClient(TEXT_MODEL, use_vision=False)
        self.ddgs = DDGS()

    def generate_shopping_list(
        self,
        instructions: Dict[str, Any],
        on_item_ready: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a shopping list.

        on_item_ready(item) is called immediately after each item's price
        is resolved — one item at a time, for real-time UI streaming.
        """
        tools = instructions.get("tools_needed", [])
        materials = instructions.get("materials_needed", [])
        all_items = tools + materials

        if not all_items:
            return {"items": [], "total_items": 0}

        print("📋 Структурирую список покупок...")
        structured = self._structure_items(all_items)
        total = len(structured)
        print(f"🔍 Ищу цены ({total} товаров)...")

        for idx, item in enumerate(structured):
            snippets = self._search_item(item["name"], idx + 1, total)
            price_info = self._extract_price_single(item["name"], snippets)
            item["estimated_price"] = price_info.get("price", 300)
            item["where_to_buy"] = price_info.get("source", "Оценка ИИ")

            if on_item_ready is not None:
                on_item_ready(item)

            if idx < total - 1:
                time.sleep(0.3)

        return {"items": structured, "total_items": len(structured)}

    def generate_shopping_list_async(
        self,
        instructions: Dict[str, Any],
        on_item_ready: Callable[[Dict[str, Any]], None],
        on_done: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> threading.Thread:
        """Run generate_shopping_list in a daemon thread. Returns the thread."""

        def _run():
            result = self.generate_shopping_list(instructions, on_item_ready)
            if on_done:
                on_done(result)

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    def _structure_items(self, raw: List[str]) -> List[Dict[str, Any]]:
        text = "\n".join(f"- {x}" for x in raw)
        prompt = (
            "Верни JSON-массив для списка товаров.\n\n"
            f"Список:\n{text}\n\n"
            "Формат (только JSON, без лишнего текста):\n"
            '[{"name":"Название","category":"инструмент" или "материал","quantity":"1 шт","optional":false}]'
        )
        try:
            resp = self.client.generate_content(prompt)
            if resp and resp.strip():
                objects = _extract_json_objects(resp)
                if objects:
                    return objects
        except Exception as e:
            logger.warning(f"Structure failed: {e}")

        mat_kw = [
            "клей",
            "лента",
            "герметик",
            "пена",
            "провод",
            "кабель",
            "прокладка",
            "шланг",
            "элемент",
            "припой",
            "трубка",
        ]
        return [
            {
                "name": x,
                "category": "материал"
                if any(k in x.lower() for k in mat_kw)
                else "инструмент",
                "quantity": "1 шт",
                "optional": False,
            }
            for x in raw
        ]

    def _search_item(self, name: str, idx: int, total: int) -> str:
        try:
            results = self.ddgs.text(
                f"{name} купить цена",
                region="ru-ru",
                max_results=5,
                backend="html",
            )
            if not results:
                print(f"   ⚠️ [{idx}/{total}] {name}: 0 результатов")
                return ""

            lines = []
            for r in results:
                title = r.get("title", "").replace("{", "").replace("}", "")
                body = r.get("body", "").replace("{", "").replace("}", "")
                url = r.get("href", "")
                store = _domain_to_store(url) if url else "?"
                if title or body:
                    lines.append(f"[{store}] {title} — {body}")

            print(f"   ✅ [{idx}/{total}] {name}: {len(results)} результатов")
            return "\n".join(lines)
        except Exception as e:
            print(f"   ❌ [{idx}/{total}] {name}: {e}")
            return ""

    def _extract_price_single(self, name: str, snippets: str) -> Dict[str, Any]:
        """One LLM call to extract price for a single item."""
        if not snippets.strip():
            return {"price": 300, "source": "Оценка ИИ"}

        prompt = (
            f"Определи розничную цену для товара: «{name}»\n\n"
            f"Результаты поиска:\n{snippets}\n\n"
            "Инструкция:\n"
            "- Бери цену за стандартную розничную упаковку (не за метр/грамм/штуку из набора).\n"
            "- Название магазина указано в [квадратных скобках] — перенеси в source.\n"
            '- Если цены нет — оцени сам, source = "Оценка ИИ".\n'
            "- Верни только JSON без лишнего текста.\n\n"
            'Формат: {"price": 1500, "source": "Ozon"}'
        )
        try:
            resp = self.client.generate_content(prompt)
            if resp and resp.strip():
                data = _parse_dict_response(resp)
                if isinstance(data, dict) and "price" in data:
                    raw = data["price"]
                    return {
                        "price": int(raw) if isinstance(raw, (int, float)) else 300,
                        "source": data.get("source", "Интернет-магазин"),
                    }
        except Exception as e:
            logger.warning(f"Price extract failed for '{name}': {e}")

        return {"price": 300, "source": "Оценка ИИ"}

    def estimate_total_cost(self, shopping_list: Dict[str, Any]) -> Dict[str, Any]:
        items = shopping_list.get("items", [])
        t_mat = sum(
            it.get("estimated_price", 0)
            for it in items
            if it.get("category") != "инструмент"
        )
        t_tool = sum(
            it.get("estimated_price", 0)
            for it in items
            if it.get("category") == "инструмент"
        )
        return {
            "total_cost": t_mat + t_tool,
            "materials_cost": t_mat,
            "tools_cost": t_tool,
            "required_items_count": sum(1 for i in items if not i.get("optional")),
            "optional_items_count": sum(1 for i in items if i.get("optional")),
            "currency": "RUB",
        }

    @staticmethod
    def format_shopping_list(
        shopping_list: Dict[str, Any], cost_estimate: Dict[str, Any]
    ) -> str:
        if not shopping_list.get("items"):
            return "*Список покупок пуст.*"
        lines = ["# 🛒 Список необходимых покупок\n"]
        for item in shopping_list["items"]:
            opt = " *(Опционально)*" if item.get("optional") else ""
            icon = "🔧" if item.get("category") == "инструмент" else "📦"
            lines.append(f"### {icon} {item['name']}{opt}")
            lines.append(f"- **Цена:** ~{item.get('estimated_price', 0)} ₽")
            lines.append(
                f"- **Где купить:** {item.get('where_to_buy', 'Строительный магазин')}"
            )
            lines.append(f"- **Кол-во:** {item.get('quantity', '1 шт')}\n")
        lines.append("---\n## 💰 Итоговая смета")
        lines.append(f"- **Материалы:** {cost_estimate['materials_cost']} ₽")
        lines.append(f"- **Инструменты:** {cost_estimate['tools_cost']} ₽")
        lines.append(f"**ИТОГО:** ~{cost_estimate['total_cost']} ₽\n")
        lines.append("*(Цены из интернет-магазинов)*")
        return "\n".join(lines)
