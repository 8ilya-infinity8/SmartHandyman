"""
Shopping list generator and real-time price estimator.
Uses DuckDuckGo search integration for live price fetching.
"""

import time
from typing import Dict, List, Any
from duckduckgo_search import DDGS
from llm_client import LLMClient
from config import TEXT_MODEL


class ShoppingAgent:
    """Agent responsible for compiling shopping lists and fetching live prices."""

    def __init__(self):
        """Initializes the LLM client and DuckDuckGo search engine."""
        self.client = LLMClient(TEXT_MODEL, use_vision=False)
        self.ddgs = DDGS()

    def generate_shopping_list(self, instructions: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts required items, structures them, and fetches current market prices."""
        tools = instructions.get("tools_needed", [])
        materials = instructions.get("materials_needed", [])
        all_items = tools + materials

        if not all_items:
            return {"items": [], "total_items": 0}

        print("📋 Структурирую список покупок через LLM...")
        structured_items = self._extract_items_structure(all_items)
        
        enriched_items = []
        for item in structured_items:
            print(f"🔄 Ищу цену для: {item['name']}...") 
            
            live_price_data = self._fetch_live_price(item["name"])
            
            item.update({
                "estimated_price": live_price_data["price"],
                "where_to_buy": live_price_data["source"],
            })
            enriched_items.append(item)
            
            time.sleep(2.5)

        return {"items": enriched_items, "total_items": len(enriched_items)}

    def _extract_items_structure(self, raw_items: List[str]) -> List[Dict[str, Any]]:
        """Uses LLM to clean up and categorize the raw list of items into a structured JSON."""
        items_text = "\n".join(f"- {item}" for item in raw_items)
        prompt = f"""
        Проанализируй список для ремонта и верни массив JSON.
        Для каждого предмета определи категорию и является ли он обязательным.
        
        Список:
        {items_text}
        
        Формат ответа (только JSON): [
            {{
                "name": "Точное название (например: Силиконовый герметик момент)",
                "category": "инструмент" или "материал",
                "quantity": "1 шт",
                "optional": false
            }}
        ]
        """
        try:
            response_text = self.client.generate_content(prompt)
            parsed = self.client.parse_json_response(response_text)
            return parsed if isinstance(parsed, list) else self._fallback_structure(raw_items)
        except Exception as e:
            print(f"❌ Ошибка при структурировании списка: {e}")
            return self._fallback_structure(raw_items)

    def _fetch_live_price(self, item_name: str) -> Dict[str, Any]:
        """Searches the web for the item to find actual current prices (RAG implementation)."""
        query = f"купить {item_name} цена руб"
        
        try:
            results = self.ddgs.text(query, region='ru-ru', max_results=4)
            
            if not results:
                print(f"   ❌ Поисковик не выдал результатов для '{item_name}'")
                raise ValueError("No search results")

            clean_snippets = []
            for r in results:
                title = r.get('title', '').replace('{', '').replace('}', '')
                body = r.get('body', '').replace('{', '').replace('}', '')
                clean_snippets.append(f"Сайт: {title} | Текст: {body}")
            
            context = "\n".join(clean_snippets)
            
            prompt = f"""Пожалуйста, помоги составить смету для домашнего ремонта. Извлеки актуальную цену для товара "{item_name}" на основе этих сниппетов из поисковика:

<search_results>
{context}
</search_results>

Инструкция:
1. Найди в тексте реалистичную цену в рублях. Если упоминается несколько цен, выбери среднюю. Если написано "от 150", используй 150.
2. Если в тексте вообще нет цен, пожалуйста, оцени примерную рыночную стоимость товара "{item_name}" самостоятельно (на основе своих знаний) и укажи источник "Оценка ИИ".
3. ВАЖНО: Укажи цену строго целым числом, округлив до рублей (без копеек, точек и запятых).
4. Пожалуйста, выведи результат ИСКЛЮЧИТЕЛЬНО в формате JSON, без какого-либо текста до или после (не пиши "Вот JSON" и т.д.).

Пример требуемого формата:
{{
    "price": 450,
    "source": "Петрович"
}}"""
            
            response = self.client.generate_content(prompt)
            data = self.client.parse_json_response(response)
            
            if data and "price" in data:
                raw_price = data["price"]
                
                if isinstance(raw_price, (int, float)):
                    clean_price = int(raw_price)
                else:
                    base_price_str = str(raw_price).replace(',', '.').split('.')[0]
                    digits_only = ''.join(filter(str.isdigit, base_price_str))
                    clean_price = int(digits_only) if digits_only else 300
                
                print(f"   ✅ Найдена цена: {clean_price} руб. ({data.get('source', 'Интернет')})")
                return {
                    "price": clean_price,
                    "source": data.get("source", "Онлайн-магазины")
                }
            else:
                response_str = str(response) if response else "Пустой или нечитаемый ответ"
                clean_error_msg = response_str.replace('\n', ' ')[:70]
                print(f"   ⚠️ LLM не дала JSON. Ответ: {clean_error_msg}...")
                
        except Exception as e:
            print(f"   ❌ Ошибка при поиске '{item_name}': {type(e).__name__} - {e}")
            
        return {"price": 300, "source": "Ориентировочная цена"}

    def _fallback_structure(self, raw_items: List[str]) -> List[Dict[str, Any]]:
        """Provides graceful degradation if the LLM fails to parse the JSON structure."""
        materials_keywords = ["клей", "лента", "герметик", "пена", "букса", "провод", "кабель", "прокладка"]
        return [
            {
                "name": item,
                "category": "материал" if any(x in item.lower() for x in materials_keywords) else "инструмент",
                "quantity": "1 шт",
                "optional": False
            } for item in raw_items
        ]

    def estimate_total_cost(self, shopping_list: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates totals dynamically based on enriched items with actual prices."""
        items = shopping_list.get("items", [])
        
        total_materials = 0
        total_tools = 0
        
        for item in items:
            price = item.get("estimated_price", 0)
            if item.get("category") == "инструмент":
                total_tools += price
            else:
                total_materials += price

        return {
            "total_cost": total_materials + total_tools,
            "materials_cost": total_materials,
            "tools_cost": total_tools,
            "required_items_count": len([i for i in items if not i.get("optional")]),
            "optional_items_count": len([i for i in items if i.get("optional")]),
            "currency": "RUB",
        }

    @staticmethod
    def format_shopping_list(shopping_list: Dict[str, Any], cost_estimate: Dict[str, Any]) -> str:
        """Formats the generated list and cost estimate cleanly for markdown rendering."""
        if not shopping_list.get("items"):
            return "*Список покупок пуст. Похоже, у вас уже всё есть!*"

        lines = ["# 🛒 Список необходимых покупок\n"]
        
        for item in shopping_list["items"]:
            req_mark = "*(Опционально)*" if item.get("optional") else ""
            icon = "🔧" if item.get("category") == "инструмент" else "📦"
            
            lines.append(f"### {icon} {item['name']} {req_mark}")
            lines.append(f"- **Цена:** ~{item.get('estimated_price', 0)} ₽")
            lines.append(f"- **Где искать:** {item.get('where_to_buy', 'Строительный магазин')}")
            lines.append(f"- **Кол-во:** {item.get('quantity', '1 шт')}\n")

        lines.append("---\n")
        lines.append("## 💰 Итоговая смета")
        lines.append(f"- **Расходные материалы:** {cost_estimate['materials_cost']} ₽")
        lines.append(f"- **Инструменты:** {cost_estimate['tools_cost']} ₽")
        lines.append(f"**ИТОГО:** ~{cost_estimate['total_cost']} ₽\n")
        
        lines.append("*(Цены собраны из открытых источников в реальном времени)*")
        
        return "\n".join(lines)
