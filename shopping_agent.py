import json
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from ddgs import DDGS
from llm_client import LLMClient
from config import TEXT_MODEL

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

class ShoppingAgent:
    def __init__(self):
        self.client = LLMClient(TEXT_MODEL, use_vision=False)
        self.ddgs = DDGS()

    def get_full_report(self, instructions: Dict[str, Any]) -> Dict[str, Any]:
        shopping_list = self.generate_shopping_list(instructions)
        cost_estimate = self.estimate_total_cost(shopping_list)
        
        final_output = {
            "shopping_list_data": shopping_list,
            "cost_estimate_data": cost_estimate
        }
        
        print(f"Финальный результат работы агента:\n{json.dumps(final_output, indent=2, ensure_ascii=False)}")
        return final_output

    def generate_shopping_list(self, instructions: Dict[str, Any]) -> Dict[str, Any]:
        tools = instructions.get("tools_needed", [])
        materials = instructions.get("materials_needed", [])
        all_items = tools + materials

        if not all_items:
            return {"items": [], "total_items": 0}

        print("📋 Структурирую список покупок (автоматически)...")
        structured = self._structure_items(all_items)

        print(f"🔍 Ищу цены ({len(structured)} товаров)...")
        self._fill_prices(structured)

        return {"items": structured, "total_items": len(structured)}

    def _structure_items(self, raw: List[str]) -> List[Dict[str, Any]]:
        mat_kw = ["клей", "лента", "герметик", "пена", "провод", "кабель", "прокладка", "шланг", "элемент", "припой", "трубка", "панель"]
        result = []
        for item in raw:
            is_material = any(keyword in item.lower() for keyword in mat_kw)
            result.append({
                "name": item, 
                "category": "материал" if is_material else "инструмент",
                "quantity": "1 шт", 
                "optional": False
            })
        return result

    def _fill_prices(self, items: List[Dict[str, Any]]) -> None:
        names = [it["name"] for it in items]
        snippets_map = {}
        search_batch_size = 5
        
        for i, name in enumerate(names):
            snippets_map[name] = self._search_item(name, i + 1, len(names))
            if i < len(names) - 1:
                if (i + 1) % search_batch_size == 0:
                    print("   ⏳ [Анти-бан] Отдыхаем 3 секунды...")
                    time.sleep(3.0)
                else:
                    time.sleep(1.5)

        found = sum(1 for v in snippets_map.values() if v)
        print(f"   📊 Результаты: {found}/{len(names)}")

        prices = self._extract_prices(names, snippets_map)

        for item in items:
            p = prices.get(item["name"], {})
            item["estimated_price"] = p.get("price", 300)
            item["where_to_buy"] = p.get("source", "Оценка ИИ")

        print(f"[DEBUG] Итоговый список товаров:\n{json.dumps(items, indent=2, ensure_ascii=False)}")

    def _search_item(self, name: str, idx: int, total: int) -> str:
        try:
            results = self.ddgs.text(
                f"{name} купить цена",
                region="ru-ru", max_results=5
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

    def _extract_prices(self, names: List[str], snippets_map: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        result = {}
        chunk_size = 5
        
        for i in range(0, len(names), chunk_size):
            chunk_names = names[i:i + chunk_size]
            sections = []
            
            for name in chunk_names:
                snip = snippets_map.get(name, "").strip()
                sections.append(f"### {name}\n{snip or '(ничего не найдено)'}")

            json_items = ",\n".join(f'    "{n}": {{"price": 0, "source": "Оценка ИИ"}}' for n in chunk_names)

            prompt = f"""Для каждого товара определи розничную цену и магазин.

{chr(10).join(sections)}

Инструкция:
- Извлеки цену из результатов поиска (целое число).
- Название магазина указано в квадратных скобках — перенеси его в "source".
- Если нет данных — оцени стоимость сам.
- Ответ — ТОЛЬКО JSON-объект.

JSON (ключи = ТОЧНЫЕ названия товаров):
{{
{json_items}
}}"""

            try:
                resp = self.client.generate_content(prompt)
                if not resp or not resp.strip():
                    continue

                data = self.client.parse_json_response(resp)
                if not isinstance(data, dict):
                    continue

                for name in chunk_names:
                    entry = data.get(name) or self._fuzzy_find(name, data)
                    
                    if isinstance(entry, dict) and "price" in entry:
                        raw_price = entry.get("price")
                        try:
                            price = int(raw_price)
                            if price <= 0: price = 300
                        except (ValueError, TypeError):
                            price = 300
                            
                        result[name] = {
                            "price": price,
                            "source": entry.get("source") or "Оценка ИИ",
                        }
                    else:
                        result[name] = {"price": 300, "source": "Оценка ИИ"}

            except Exception as e:
                print(f"[ERROR] Price extraction failed for chunk: {e}")
                for name in chunk_names:
                    result[name] = {"price": 300, "source": "Оценка ИИ"}
                    
        real = sum(1 for v in result.values() if v["source"] != "Оценка ИИ")
        print(f"   💰 Цены: {real}/{len(names)} из магазинов")
        return result

    @staticmethod
    def _fuzzy_find(target: str, data: Dict) -> Optional[Dict]:
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