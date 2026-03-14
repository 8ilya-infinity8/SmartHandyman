#!/usr/bin/env python3
"""
Генератор HTML-отчета с графиками по вычислительным потребностям.
"""

import json
from pathlib import Path


def generate_html_report(json_path: str, output_path: str):
    """Генерирует красивый HTML отчет с графиками."""

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    # Подготовка данных для модулей
    modules = data.get("modules", {})
    module_names = list(modules.keys())
    module_memory = [modules[m].get("peak_memory_mb", 0) for m in module_names]
    module_import = [modules[m].get("import_time_sec", 0) for m in module_names]

    # Данные зависимостей
    deps = data.get("dependencies", {})
    heavy_packages = deps.get("heavy_packages", [])
    heavy_names = [p["name"] for p in heavy_packages]
    heavy_weights = [p["weight_mb"] for p in heavy_packages]

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Отчет о вычислительных потребностях - SmartHandyman</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #e0e0e0;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }}
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #888;
            font-size: 1.1rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        .card {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .card h2 {{
            font-size: 1.4rem;
            margin-bottom: 20px;
            color: #00d9ff;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .card h2::before {{
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(180deg, #00d9ff, #00ff88);
            border-radius: 2px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }}
        .stat-item {{
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 1.8rem;
            font-weight: bold;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-label {{
            font-size: 0.85rem;
            color: #888;
            margin-top: 5px;
        }}
        .chart-container {{
            position: relative;
            height: 300px;
            margin-top: 20px;
        }}
        .table-container {{
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            background: rgba(0,217,255,0.1);
            color: #00d9ff;
            font-weight: 600;
        }}
        tr:hover {{
            background: rgba(255,255,255,0.03);
        }}
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-ml {{ background: rgba(255,99,132,0.2); color: #ff6384; }}
        .badge-api {{ background: rgba(54,162,235,0.2); color: #36a2eb; }}
        .badge-web {{ background: rgba(255,206,86,0.2); color: #ffce56; }}
        .recommendations {{
            background: rgba(0,255,136,0.05);
            border: 1px solid rgba(0,255,136,0.2);
            border-radius: 15px;
            padding: 25px;
            margin-top: 30px;
        }}
        .recommendations h2 {{
            color: #00ff88;
            margin-bottom: 20px;
        }}
        .rec-item {{
            display: flex;
            align-items: flex-start;
            gap: 15px;
            padding: 15px;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            margin-bottom: 10px;
        }}
        .rec-icon {{
            font-size: 1.5rem;
        }}
        .rec-content h3 {{
            font-size: 1rem;
            color: #e0e0e0;
            margin-bottom: 5px;
        }}
        .rec-content p {{
            font-size: 0.9rem;
            color: #888;
        }}
        .full-width {{
            grid-column: 1 / -1;
        }}
        .memory-bar {{
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .memory-fill {{
            height: 100%;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        @media (max-width: 768px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            .stat-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 SmartHandyman - Анализ вычислительных потребностей</h1>
            <p>Дата анализа: {data["timestamp"].split("T")[0]}</p>
        </div>

        <div class="grid">
            <!-- System Info -->
            <div class="card">
                <h2>Системная информация</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{data["system_info"]["cpu_physical"]}</div>
                        <div class="stat-label">Физических ядер</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{data["system_info"]["cpu_count"]}</div>
                        <div class="stat-label">Логических ядер</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{data["system_info"]["memory_available_gb"]}</div>
                        <div class="stat-label">Доступно RAM (ГБ)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{data["system_info"]["memory_total_gb"]}</div>
                        <div class="stat-label">Всего RAM (ГБ)</div>
                    </div>
                </div>
            </div>

            <!-- Dependencies Summary -->
            <div class="card">
                <h2>Зависимости</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{deps.get("total_packages", 0)}</div>
                        <div class="stat-label">Всего пакетов</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{deps.get("estimated_base_memory_mb", 0)}</div>
                        <div class="stat-label">Память зависимостей (МБ)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(deps.get("ml_packages", []))}</div>
                        <div class="stat-label">ML пакеты</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{len(deps.get("api_packages", []))}</div>
                        <div class="stat-label">API пакеты</div>
                    </div>
                </div>
            </div>

            <!-- Memory by Module Chart -->
            <div class="card">
                <h2>Память по модулям</h2>
                <div class="chart-container">
                    <canvas id="memoryChart"></canvas>
                </div>
            </div>

            <!-- Import Time Chart -->
            <div class="card">
                <h2>Время импорта модулей</h2>
                <div class="chart-container">
                    <canvas id="importChart"></canvas>
                </div>
            </div>

            <!-- Heavy Packages Chart -->
            <div class="card full-width">
                <h2>Тяжелые пакеты (потребление памяти)</h2>
                <div class="chart-container">
                    <canvas id="heavyChart"></canvas>
                </div>
            </div>

            <!-- Modules Detail Table -->
            <div class="card full-width">
                <h2>Детальная информация по модулям</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Модуль</th>
                                <th>Время импорта (сек)</th>
                                <th>Базовая память (МБ)</th>
                                <th>Пиковая память (МБ)</th>
                                <th>Классов</th>
                                <th>Функций</th>
                            </tr>
                        </thead>
                        <tbody>
                            {generate_module_rows(modules)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Heavy Packages Table -->
            <div class="card full-width">
                <h2>Тяжелые пакеты</h2>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Пакет</th>
                                <th>Потребление памяти (МБ)</th>
                                <th>Категория</th>
                            </tr>
                        </thead>
                        <tbody>
                            {generate_package_rows(deps)}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Recommendations -->
        <div class="recommendations">
            <h2>📋 Рекомендации</h2>
            <div class="rec-item">
                <span class="rec-icon">✅</span>
                <div class="rec-content">
                    <h3>Минимальные требования</h3>
                    <p>2 CPU ядра, 2 ГБ RAM - достаточно для локальной разработки и тестирования</p>
                </div>
            </div>
            <div class="rec-item">
                <span class="rec-icon">🚀</span>
                <div class="rec-content">
                    <h3>Рекомендуемые требования</h3>
                    <p>4 CPU ядра, 4 ГБ RAM - комфортная работа с запасом</p>
                </div>
            </div>
            <div class="rec-item">
                <span class="rec-icon">🏭</span>
                <div class="rec-content">
                    <h3>Для продакшена</h3>
                    <p>8 CPU ядер, 8 ГБ RAM - для 10+ одновременных пользователей</p>
                </div>
            </div>
            <div class="rec-item">
                <span class="rec-icon">💡</span>
                <div class="rec-content">
                    <h3>Ключевые потребители памяти</h3>
                    <p>Streamlit (~250 МБ), Pandas+PyArrow (~270 МБ), RAG embedding (~300 МБ)</p>
                </div>
            </div>
            <div class="rec-item">
                <span class="rec-icon">⚡</span>
                <div class="rec-content">
                    <h3>GPU не требуется</h3>
                    <p>Все тяжелые модели (LLM, Vision) работают через API. Локально только легкая embedding модель</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Memory by Module Chart
        new Chart(document.getElementById('memoryChart'), {{
            type: 'bar',
            data: {{
                labels: {json.dumps(module_names)},
                datasets: [{{
                    label: 'Память (МБ)',
                    data: {json.dumps(module_memory)},
                    backgroundColor: 'rgba(0, 217, 255, 0.6)',
                    borderColor: 'rgba(0, 217, 255, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: 'rgba(255, 255, 255, 0.1)'
                        }},
                        ticks: {{
                            color: '#888'
                        }}
                    }},
                    x: {{
                        grid: {{
                            display: false
                        }},
                        ticks: {{
                            color: '#888'
                        }}
                    }}
                }}
            }}
        }});

        // Import Time Chart
        new Chart(document.getElementById('importChart'), {{
            type: 'line',
            data: {{
                labels: {json.dumps(module_names)},
                datasets: [{{
                    label: 'Время импорта (сек)',
                    data: {json.dumps(module_import)},
                    backgroundColor: 'rgba(0, 255, 136, 0.2)',
                    borderColor: 'rgba(0, 255, 136, 1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{
                            color: 'rgba(255, 255, 255, 0.1)'
                        }},
                        ticks: {{
                            color: '#888'
                        }}
                    }},
                    x: {{
                        grid: {{
                            display: false
                        }},
                        ticks: {{
                            color: '#888'
                        }}
                    }}
                }}
            }}
        }});

        // Heavy Packages Chart
        new Chart(document.getElementById('heavyChart'), {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps(heavy_names)},
                datasets: [{{
                    data: {json.dumps(heavy_weights)},
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.7)',
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 206, 86, 0.7)',
                        'rgba(75, 192, 192, 0.7)',
                        'rgba(153, 102, 255, 0.7)',
                        'rgba(255, 159, 64, 0.7)',
                        'rgba(199, 199, 199, 0.7)',
                        'rgba(83, 102, 255, 0.7)',
                        'rgba(255, 99, 255, 0.7)'
                    ],
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            color: '#e0e0e0'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"📊 HTML отчет создан: {output_path}")


def generate_module_rows(modules: dict) -> str:
    """Генерирует строки таблицы модулей."""
    rows = []
    for name, data in modules.items():
        rows.append(f"""
            <tr>
                <td><code>{name}</code></td>
                <td>{data.get("import_time_sec", 0):.3f}</td>
                <td>{data.get("base_memory_mb", 0):.2f}</td>
                <td>{data.get("peak_memory_mb", 0):.2f}</td>
                <td>{len(data.get("classes", []))}</td>
                <td>{len(data.get("functions", []))}</td>
            </tr>
        """)
    return "\n".join(rows)


def generate_package_rows(deps: dict) -> str:
    """Генерирует строки таблицы пакетов."""
    rows = []
    deps.get("ml_packages", [])
    api_packages = deps.get("api_packages", [])
    web_packages = deps.get("web_packages", [])

    for pkg in deps.get("heavy_packages", []):
        name = pkg["name"]
        category = "ml"
        if name in api_packages:
            category = "api"
        elif name in web_packages:
            category = "web"

        badge_class = f"badge-{category}"
        rows.append(f"""
            <tr>
                <td><code>{name}</code></td>
                <td>{pkg["weight_mb"]}</td>
                <td><span class="badge {badge_class}">{category.upper()}</span></td>
            </tr>
        """)
    return "\n".join(rows)


if __name__ == "__main__":
    json_path = "./profiling_results/compute_analysis.json"
    output_path = "./profiling_results/compute_report.html"

    if Path(json_path).exists():
        generate_html_report(json_path, output_path)
    else:
        print(f"❌ Файл {json_path} не найден. Сначала запустите compute_analyzer.py")
