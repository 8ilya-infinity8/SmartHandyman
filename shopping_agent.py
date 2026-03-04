"""Shopping list generator and price estimator agent."""

from llm_client import LLMClient
from config import TEXT_MODEL
import requests
import json


class ShoppingAgent:
    """Generates shopping list and estimates prices."""

    def __init__(self):
        self.client = LLMClient(TEXT_MODEL, use_vision=False)

    def generate_shopping_list(self, instructions):
        """
        Generate detailed shopping list from repair instructions.

        Args:
            instructions: Repair instructions with tools and materials

        Returns:
            dict with shopping list
        """
        tools = instructions.get("tools_needed", [])
        materials = instructions.get("materials_needed", [])

        all_items = tools + materials

        if not all_items:
            return {"items": [], "total_items": 0}

        prompt = f"""Создай детальный список покупок для ремонта.

Необходимые инструменты и материалы:
{chr(10).join(f"- {item}" for item in all_items)}

Для каждого предмета укажи:
- Точное название
- Категорию (инструмент/материал)
- Примерную цену в рублях
- Где купить (тип магазина)
- Альтернативы если есть

Верни в формате JSON:
{{
    "items": [
        {{
            "name": "название",
            "category": "инструмент/материал",
            "estimated_price": цена_в_рублях,
            "where_to_buy": "тип магазина",
            "alternatives": ["альтернатива 1"],
            "quantity": "количество",
            "optional": true/false
        }}
    ]
}}"""

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            if result:
                result["total_items"] = len(result.get("items", []))
                return result
            else:
                # JSON parsing failed - parse text manually
                return self._parse_text_shopping_list(response_text, all_items)

        except Exception as e:
            # Fallback: create basic list with estimated prices
            items = []
            for item in all_items:
                # Try to estimate basic prices
                price = self._estimate_basic_price(item)
                items.append(
                    {
                        "name": item,
                        "category": self._guess_category(item),
                        "estimated_price": price,
                        "where_to_buy": "Строительный магазин или хозяйственный",
                        "quantity": "1",
                        "optional": False,
                    }
                )

            return {"items": items, "total_items": len(items), "error": str(e)}

    def _parse_text_shopping_list(self, text, all_items):
        """Parse shopping list from plain text when JSON parsing fails."""
        items = []

        # Try to extract prices from text
        import re

        for item_name in all_items:
            # Look for price mentions near the item name
            price = 0
            category = self._guess_category(item_name)

            # Try to find price in text
            pattern = rf"{re.escape(item_name)}.*?(\d+)\s*(?:руб|₽|rub)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price = int(match.group(1))
            else:
                # Use basic estimation
                price = self._estimate_basic_price(item_name)

            items.append(
                {
                    "name": item_name,
                    "category": category,
                    "estimated_price": price,
                    "where_to_buy": "Строительный магазин, Леруа Мерлен, Озон",
                    "quantity": "1",
                    "optional": False,
                }
            )

        return {"items": items, "total_items": len(items), "raw_text": text}

    def _guess_category(self, item_name):
        """Guess item category from name."""
        item_lower = item_name.lower()

        tools = [
            "ключ",
            "отвертка",
            "молоток",
            "плоскогубцы",
            "пассатижи",
            "дрель",
            "шуруповерт",
            "уровень",
            "рулетка",
        ]

        if any(tool in item_lower for tool in tools):
            return "инструмент"
        return "материал"

    def _estimate_basic_price(self, item_name):
        """Estimate basic price for common items."""
        item_lower = item_name.lower()

        # Price estimation based on common items
        if "лента" in item_lower or "скотч" in item_lower:
            return 50
        elif "герметик" in item_lower:
            return 200
        elif "прокладка" in item_lower:
            return 100
        elif "ключ" in item_lower:
            return 300
        elif "отвертка" in item_lower:
            return 150
        elif "фильтр" in item_lower:
            return 500
        elif "шланг" in item_lower:
            return 300
        elif "кран" in item_lower or "смеситель" in item_lower:
            return 1500
        elif "провод" in item_lower or "кабель" in item_lower:
            return 100
        else:
            return 200  # Default estimate

    def estimate_total_cost(self, shopping_list):
        """
        Estimate total repair cost.

        Args:
            shopping_list: Shopping list with items and prices

        Returns:
            dict with cost breakdown
        """
        items = shopping_list.get("items", [])

        total_materials = 0
        total_tools = 0
        required_items = []
        optional_items = []

        for item in items:
            price = item.get("estimated_price", 0)
            category = item.get("category", "материал")
            is_optional = item.get("optional", False)

            if is_optional:
                optional_items.append(item)
            else:
                required_items.append(item)

            if category == "инструмент":
                total_tools += price
            else:
                total_materials += price

        total = total_materials + total_tools

        return {
            "total_cost": total,
            "materials_cost": total_materials,
            "tools_cost": total_tools,
            "required_items_count": len(required_items),
            "optional_items_count": len(optional_items),
            "currency": "RUB",
        }

    def search_online_prices(self, item_name):
        """
        Search for actual prices online (simulated).
        In production, this would scrape real store websites or use APIs.
        """
        # This is a placeholder for actual price search
        # In production, you'd integrate with store APIs or web scraping
        prompt = f"""Найди примерные актуальные цены на товар: {item_name}

Укажи цены в популярных магазинах (Леруа Мерлен, Озон, Wildberries, местные строительные).

Верни в формате JSON:
{{
    "item": "{item_name}",
    "prices": [
        {{
            "store": "название магазина",
            "price": цена,
            "url": "ссылка если есть"
        }}
    ],
    "average_price": средняя_цена
}}"""

        try:
            response_text = self.client.generate_content(prompt)
            result = self.client.parse_json_response(response_text)

            if result:
                return result
            else:
                return {
                    "item": item_name,
                    "prices": [],
                    "average_price": 0,
                    "note": "Не удалось найти актуальные цены",
                }

        except:
            return {
                "item": item_name,
                "prices": [],
                "average_price": 0,
                "note": "Не удалось найти актуальные цены",
            }

    def format_shopping_list(self, shopping_list, cost_estimate):
        """Format shopping list for display."""
        output = ["# 🛒 Список покупок"]

        items = shopping_list.get("items", [])

        # Required items
        required = [item for item in items if not item.get("optional", False)]
        if required:
            output.append("\n## Необходимые покупки:")
            for item in required:
                price = item.get("estimated_price", 0)
                output.append(f"\n**{item['name']}** - ~{price} ₽")
                output.append(f"  - Количество: {item.get('quantity', '1')}")
                output.append(f"  - Где купить: {item.get('where_to_buy', 'Магазин')}")
                if item.get("alternatives"):
                    output.append(
                        f"  - Альтернативы: {', '.join(item['alternatives'])}"
                    )

        # Optional items
        optional = [item for item in items if item.get("optional", False)]
        if optional:
            output.append("\n## Опциональные покупки:")
            for item in optional:
                price = item.get("estimated_price", 0)
                output.append(f"\n**{item['name']}** - ~{price} ₽")

        # Cost summary
        output.append("\n## 💰 Примерная стоимость:")
        output.append(f"- Материалы: {cost_estimate['materials_cost']} ₽")
        output.append(f"- Инструменты: {cost_estimate['tools_cost']} ₽")
        output.append(f"**Итого: ~{cost_estimate['total_cost']} ₽**")

        output.append(
            "\n*Цены приблизительные и могут отличаться в зависимости от региона и магазина.*"
        )

        return "\n".join(output)
