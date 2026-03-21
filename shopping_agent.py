"""
Shopping list generator and price estimator.
Sequential per-item DuckDuckGo search + single LLM call for price extraction.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from ddgs import DDGS
from llm_client import LLMClient
from config import TEXT_MODEL

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
    """Extract store name from URL."""
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


class ShoppingAgent:
    """Compiles shopping lists and estimates prices from real sources."""

    def __init__(self):
        self.client = LLMClient(TEXT_MODEL, use_vision=False)
        self.ddgs = DDGS()

    def generate_shopping_list(self, instructions: Dict[str, Any]) -> Dict[str, Any]:
        tools = instructions.get("tools_needed", [])
        materials = instructions.get("materials_needed", [])
        all_items = tools + materials

        if not all_items:
            return {"items": [], "total_items": 0}

        print("📋 Структурирую список покупок...")
        structured = self._structure_items(all_items)

        print(f"🔍 Ищу цены ({len(structured)} товаров)...")
        self._fill_prices(structured)

        return {"items": structured, "total_items": len(structured)}

    def _structure_items(self, raw: List[str]) -> List[Dict[str, Any]]:
        text = "\n".join(f"- {x}" for x in raw)
        prompt = (
            "Верни JSON-массив для списка товаров.\n\n"
            f"Список:\n{text}\n\n"
            'Формат (только JSON): [{"name":"Название","category":"инструмент" или "материал","quantity":"1 шт","optional":false}]'
        )
        try:
            resp = self.client.generate_content(prompt)
            parsed = self.client.parse_json_response(resp)
            if isinstance(parsed, list) and parsed:
                return parsed
        except Exception as e:
            logger.warning(f"Structure failed: {e}")

        mat_kw = ["клей","лента","герметик","пена","провод","кабель","прокладка","шланг","элемент","припой","трубка"]
        return [
            {"name": x, "category": "материал" if any(k in x.lower() for k in mat_kw) else "инструмент",
             "quantity": "1 шт", "optional": False}
            for x in raw
        ]

    def _fill_prices(self, items: List[Dict[str, Any]]) -> None:
        """Search each item, then one LLM call to extract all prices."""
        names = [it["name"] for it in items]

        snippets_map = {}
        for i, name in enumerate(names):
            snippets_map[name] = self._search_item(name, i + 1, len(names))
            if i < len(names) - 1:
                time.sleep(0.8)

        found = sum(1 for v in snippets_map.values() if v)
        print(f"   📊 Результаты: {found}/{len(names)}")

        prices = self._extract_prices(names, snippets_map)

        for item in items:
            p = prices.get(item["name"], {})
            item["estimated_price"] = p.get("price", 300)
            item["where_to_buy"] = p.get("source", "Оценка ИИ")

    def _search_item(self, name: str, idx: int, total: int) -> str:
        """Search DuckDuckGo for one item. Returns formatted snippets."""
        try:
            results = self.ddgs.text(
                f"{name} купить цена",
                region="ru-ru", max_results=5, backend="html",
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

    def _extract_prices(
        self, names: List[str], snippets_map: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """Single LLM call: extract one price per item from search snippets."""

        sections = []
        for name in names:
            snip = snippets_map.get(name, "").strip()
            sections.append(f"### {name}\n{snip or '(ничего не найдено)'}")

        prompt = f"""Для каждого товара определи розничную цену и магазин.

{chr(10).join(sections)}

Инструкция:
- Извлеки цену из результатов поиска. Бери цену за стандартную розничную упаковку, а не за метр, грамм или поштучно из набора.
- Название магазина уже указано в квадратных скобках — просто перенеси его в "source".
- Если нет данных — оцени стоимость сам, source = "Оценка ИИ".
- Цены — целые числа в рублях.

JSON (ключи = ТОЧНЫЕ названия товаров):
{{
{chr(10).join(f'    "{n}": {{"price": 0, "source": ""}},' for n in names)}
}}"""

        try:
            resp = self.client.generate_content(prompt)
            if not resp or not resp.strip():
                return {}

            data = self.client.parse_json_response(resp)
            if not isinstance(data, dict):
                return {}

            result = {}
            for name in names:
                entry = data.get(name)
                if not entry:
                    entry = self._fuzzy_find(name, data)
                if isinstance(entry, dict) and "price" in entry:
                    raw = entry["price"]
                    price = int(raw) if isinstance(raw, (int, float)) else 300
                    result[name] = {
                        "price": price,
                        "source": entry.get("source", "Интернет-магазин"),
                    }
                else:
                    result[name] = {"price": 300, "source": "Оценка ИИ"}

            real = sum(1 for v in result.values() if v["source"] != "Оценка ИИ")
            print(f"   💰 Цены: {real}/{len(names)} из магазинов")
            return result

        except Exception as e:
            logger.error(f"Price extraction failed: {e}")
            return {}

    @staticmethod
    def _fuzzy_find(target: str, data: Dict) -> Optional[Dict]:
        """LLM sometimes tweaks keys. Find a close match."""
        tl = target.lower()
        for key, val in data.items():
            if not isinstance(val, dict):
                continue
            kl = key.lower()
            if tl in kl or kl in tl:
                return val
        return None

    def estimate_total_cost(self, shopping_list: Dict[str, Any]) -> Dict[str, Any]:
        items = shopping_list.get("items", [])
        t_mat = sum(it.get("estimated_price", 0) for it in items if it.get("category") != "инструмент")
        t_tool = sum(it.get("estimated_price", 0) for it in items if it.get("category") == "инструмент")
        return {
            "total_cost": t_mat + t_tool,
            "materials_cost": t_mat,
            "tools_cost": t_tool,
            "required_items_count": sum(1 for i in items if not i.get("optional")),
            "optional_items_count": sum(1 for i in items if i.get("optional")),
            "currency": "RUB",
        }

    @staticmethod
    def format_shopping_list(shopping_list: Dict[str, Any], cost_estimate: Dict[str, Any]) -> str:
        if not shopping_list.get("items"):
            return "*Список покупок пуст.*"

        lines = ["# 🛒 Список необходимых покупок\n"]
        for item in shopping_list["items"]:
            opt = " *(Опционально)*" if item.get("optional") else ""
            icon = "🔧" if item.get("category") == "инструмент" else "📦"
            lines.append(f"### {icon} {item['name']}{opt}")
            lines.append(f"- **Цена:** ~{item.get('estimated_price', 0)} ₽")
            lines.append(f"- **Где купить:** {item.get('where_to_buy', 'Строительный магазин')}")
            lines.append(f"- **Кол-во:** {item.get('quantity', '1 шт')}\n")

        lines.append("---\n## 💰 Итоговая смета")
        lines.append(f"- **Материалы:** {cost_estimate['materials_cost']} ₽")
        lines.append(f"- **Инструменты:** {cost_estimate['tools_cost']} ₽")
        lines.append(f"**ИТОГО:** ~{cost_estimate['total_cost']} ₽\n")
        lines.append("*(Цены из интернет-магазинов)*")
        return "\n".join(lines)
