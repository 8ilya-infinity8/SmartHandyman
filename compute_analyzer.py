#!/usr/bin/env python3
"""
Комплексный анализ вычислительных потребностей проекта SmartHandyman.
Анализирует использование памяти, CPU и зависимости модулей.
"""

import sys
import json
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

import psutil

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent))


class ComputeAnalyzer:
    """Анализатор вычислительных потребностей."""

    def __init__(self, output_dir: str = "./profiling_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "modules": {},
            "dependencies": {},
        }

    def _get_system_info(self) -> dict:
        """Получить информацию о системе."""
        return {
            "cpu_count": psutil.cpu_count(logical=True),
            "cpu_physical": psutil.cpu_count(logical=False),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(
                psutil.virtual_memory().available / (1024**3), 2
            ),
            "python_version": sys.version,
            "platform": sys.platform,
        }

    def analyze_module(self, name: str, module_path: str, test_func=None) -> dict:
        """Анализировать отдельный модуль."""
        print(f"\n🔍 Анализ модуля: {name}")

        result = {
            "name": name,
            "path": module_path,
            "import_time_sec": 0,
            "base_memory_mb": 0,
            "peak_memory_mb": 0,
            "classes": [],
            "functions": [],
        }

        # Измеряем время импорта
        start = time.perf_counter()
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location(name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result["import_time_sec"] = round(time.perf_counter() - start, 3)
        except Exception as e:
            result["import_error"] = str(e)
            print(f"   ⚠️ Ошибка импорта: {e}")
            return result

        # Измеряем память
        tracemalloc.start()
        process = psutil.Process()
        base_mem = process.memory_info().rss / (1024**2)

        # Если есть тестовая функция - выполняем
        if test_func:
            try:
                test_func(module)
            except Exception as e:
                result["test_error"] = str(e)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        result["base_memory_mb"] = round(base_mem, 2)
        result["peak_memory_mb"] = round(base_mem + peak / (1024**2), 2)
        result["allocated_memory_mb"] = round(peak / (1024**2), 2)

        # Ищем классы и функции
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type):
                result["classes"].append(attr_name)
            elif callable(attr) and not attr_name.startswith("_"):
                result["functions"].append(attr_name)

        print(f"   ⏱️ Время импорта: {result['import_time_sec']} сек")
        print(f"   💾 Память (базовая): {result['base_memory_mb']} МБ")
        print(f"   💾 Память (пик): {result['peak_memory_mb']} МБ")
        print(f"   📦 Классов: {len(result['classes'])}")
        print(f"   📦 Функций: {len(result['functions'])}")

        return result

    def analyze_dependencies(self, requirements_file: str) -> dict:
        """Анализировать зависимости."""
        print("\n📦 Анализ зависимостей...")

        result = {
            "total_packages": 0,
            "heavy_packages": [],
            "ml_packages": [],
            "api_packages": [],
            "web_packages": [],
        }

        req_path = Path(requirements_file)
        if not req_path.exists():
            print(f"   ⚠️ Файл {requirements_file} не найден")
            return result

        # Категории пакетов
        ml_packages = {
            "numpy",
            "pandas",
            "pyarrow",
            "pillow",
            "scikit-learn",
            "torch",
            "tensorflow",
            "sentence-transformers",
            "faiss",
        }
        api_packages = {"openai", "anthropic", "httpx", "requests"}
        web_packages = {"streamlit", "fastapi", "uvicorn", "flask"}

        packages = []
        with open(req_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    # Извлекаем имя пакета (без версии)
                    pkg_name = line.split("==")[0].split(">=")[0].split("<")[0]
                    packages.append(pkg_name.lower())

                    if pkg_name.lower() in ml_packages:
                        result["ml_packages"].append(pkg_name)
                    elif pkg_name.lower() in api_packages:
                        result["api_packages"].append(pkg_name)
                    elif pkg_name.lower() in web_packages:
                        result["web_packages"].append(pkg_name)

        result["total_packages"] = len(packages)

        # Тяжелые пакеты (оценка по известным данным)
        heavy_weights = {
            "pandas": 150,
            "numpy": 80,
            "pyarrow": 120,
            "pillow": 40,
            "streamlit": 250,
            "torch": 800,
            "tensorflow": 500,
            "sentence-transformers": 400,
            "faiss": 80,
        }

        total_weight = 0
        for pkg in packages:
            if pkg in heavy_weights:
                result["heavy_packages"].append(
                    {"name": pkg, "weight_mb": heavy_weights[pkg]}
                )
                total_weight += heavy_weights[pkg]

        result["estimated_base_memory_mb"] = total_weight

        print(f"   📦 Всего пакетов: {result['total_packages']}")
        print(f"   🧠 ML пакетов: {len(result['ml_packages'])}")
        print(f"   🌐 API пакетов: {len(result['api_packages'])}")
        print(f"   🌍 Web пакетов: {len(result['web_packages'])}")
        print(f"   💾 Оценка памяти: ~{total_weight} МБ")

        return result

    def generate_report(self) -> str:
        """Сгенерировать итоговый отчет."""
        total_memory = 0
        modules_report = []

        for name, data in self.results["modules"].items():
            mem = data.get("peak_memory_mb", 0)
            total_memory += mem
            modules_report.append(
                f"  {name}:\n"
                f"    - Импорт: {data.get('import_time_sec', 'N/A')} сек\n"
                f"    - Память: {data.get('base_memory_mb', 0)} → {mem} МБ\n"
                f"    - Классов: {len(data.get('classes', []))}\n"
                f"    - Функций: {len(data.get('functions', []))}"
            )

        deps = self.results["dependencies"]

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║  ОТЧЕТ О ВЫЧИСЛИТЕЛЬНЫХ ПОТРЕБНОСТЯХ SmartHandyman          ║
╚══════════════════════════════════════════════════════════════╝

📅 Дата: {self.results["timestamp"]}

────────────────────────────────────────────────────────────────
🖥️  СИСТЕМНАЯ ИНФОРМАЦИЯ
────────────────────────────────────────────────────────────────
  CPU: {self.results["system_info"]["cpu_physical"]} физических / {self.results["system_info"]["cpu_count"]} логических ядра
  RAM: {self.results["system_info"]["memory_available_gb"]} / {self.results["system_info"]["memory_total_gb"]} ГБ доступно
  Python: {self.results["system_info"]["python_version"].split()[0]}

────────────────────────────────────────────────────────────────
📊 АНАЛИЗ МОДУЛЕЙ
────────────────────────────────────────────────────────────────
{chr(10).join(modules_report)}

────────────────────────────────────────────────────────────────
📦 ЗАВИСИМОСТИ
────────────────────────────────────────────────────────────────
  Всего пакетов: {deps.get("total_packages", 0)}
  ML пакеты: {", ".join(deps.get("ml_packages", [])[:5])}{"..." if len(deps.get("ml_packages", [])) > 5 else ""}
  API пакеты: {", ".join(deps.get("api_packages", []))}
  Web пакеты: {", ".join(deps.get("web_packages", []))}
  Тяжелые пакеты: {len(deps.get("heavy_packages", []))}

────────────────────────────────────────────────────────────────
💾 ОЦЕНКА ПОТРЕБЛЕНИЯ ПАМЯТИ
────────────────────────────────────────────────────────────────
  Базовое (Python + зависимости): ~{deps.get("estimated_base_memory_mb", 0)} МБ
  Модули проекта: ~{total_memory} МБ
  RAG (embedding + FAISS): ~300-400 МБ (оценка)
  Streamlit сессии: ~50-100 МБ на пользователя
  ─────────────────────────────────────────────────
  ИТОГО минимум: ~{deps.get("estimated_base_memory_mb", 0) + total_memory + 400} МБ
  ИТОГО рекомендовано: ~{int((deps.get("estimated_base_memory_mb", 0) + total_memory + 400) * 1.5)} МБ (с запасом 50%)

────────────────────────────────────────────────────────────────
🎯 РЕКОМЕНДАЦИИ
────────────────────────────────────────────────────────────────
  ✅ Минимальные требования: 2 CPU ядра, 2 ГБ RAM
  ✅ Рекомендуемые: 4 CPU ядра, 4 ГБ RAM
  ✅ Для продакшена (10+ пользователей): 8 CPU ядер, 8 ГБ RAM
  
  🔥 Основные потребители памяти:
     1. Streamlit фреймворк (~250 МБ)
     2. Pandas + PyArrow (~270 МБ)
     3. RAG embedding модель (~300 МБ)
  
  ⚡ Оптимизация:
     - RAG загружается как синглтон (1 раз за процесс)
     - Нет локальных LLM (все через API)
     - GPU не требуется

────────────────────────────────────────────────────────────────
📈 СЕТЕВЫЕ ТРЕБОВАНИЯ
────────────────────────────────────────────────────────────────
  LLM API (Claude/OpenAI): 4-6 вызовов на диагностику
  DuckDuckGo поиск: N товаров × 1 запрос
  Задержки: 2-5 сек на API вызов
  
  Общее время диагностики: 30-60 секунд

═══════════════════════════════════════════════════════════════
"""

        # Сохраняем отчет
        report_path = self.output_dir / "compute_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        # Сохраняем JSON
        json_path = self.output_dir / "compute_analysis.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n📁 Отчет сохранен: {report_path}")
        print(f"📁 JSON данные: {json_path}")

        return report


def test_vision_analyzer(module):
    """Тест для vision_analyzer."""
    pass  # Инициализация без реальных вызовов API


def test_diagnostic_agent(module):
    """Тест для diagnostic_agent."""
    pass


def test_rag_retriever(module):
    """Тест для RAG retriever."""
    pass


def main():
    """Запуск анализа."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  АНАЛИЗ ВЫЧИСЛИТЕЛЬНЫХ ПОТРЕБНОСТЕЙ                         ║")
    print("║  SmartHandyman - Помощник по ремонту                        ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    analyzer = ComputeAnalyzer()

    # Анализируем зависимости
    analyzer.results["dependencies"] = analyzer.analyze_dependencies(
        "./requirements.txt"
    )

    # Анализируем основные модули
    modules_to_analyze = [
        ("config", "./config.py", None),
        ("llm_client", "./llm_client.py", None),
        ("vision_analyzer", "./vision_analyzer.py", test_vision_analyzer),
        ("diagnostic_agent", "./diagnostic_agent.py", test_diagnostic_agent),
        ("safety_checker", "./safety_checker.py", None),
        ("instruction_generator", "./instruction_generator.py", None),
        ("shopping_agent", "./shopping_agent.py", None),
    ]

    for name, path, test_func in modules_to_analyze:
        if Path(path).exists():
            result = analyzer.analyze_module(name, path, test_func)
            analyzer.results["modules"][name] = result
        else:
            print(f"\n⚠️ Модуль {path} не найден, пропускаем")

    # Генерируем отчет
    print("\n" + "=" * 60)
    report = analyzer.generate_report()
    print(report)

    return analyzer


if __name__ == "__main__":
    main()
