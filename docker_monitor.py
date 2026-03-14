#!/usr/bin/env python3
"""
Мониторинг вычислительных потребностей запущенного Docker-контейнера.
Собирает метрики CPU, RAM, сети и генерирует красивый HTML отчет.
"""

import subprocess
import json
import time
import signal
import sys
from pathlib import Path
from datetime import datetime


class DockerMonitor:
    """Монитор ресурсов Docker контейнера."""

    def __init__(self, container_name: str = "smarthandyman_app"):
        self.container_name = container_name
        self.metrics = {
            "timestamps": [],
            "cpu_percent": [],
            "memory_usage_mb": [],
            "memory_limit_mb": [],
            "memory_percent": [],
            "network_rx_mb": [],
            "network_tx_mb": [],
            "block_read_mb": [],
            "block_write_mb": [],
        }
        self.start_time = None
        self.running = False

    def check_container_running(self) -> bool:
        """Проверяет, запущен ли контейнер."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "--format={{.State.Running}}",
                    self.container_name,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip().lower() == "true"
        except Exception:
            return False

    def get_stats(self) -> dict | None:
        """Получает текущие метрики контейнера."""
        try:
            result = subprocess.run(
                [
                    "docker",
                    "stats",
                    "--no-stream",
                    "--format",
                    "{{json .}}",
                    self.container_name,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                print(f"⚠️ Ошибка получения статистики: {result.stderr}")
                return None

            data = json.loads(result.stdout)
            return self._parse_stats(data)

        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            return None

    def _parse_stats(self, data: dict) -> dict:
        """Парсит сырые данные статистики."""
        try:
            # CPU (поддержка разных форматов)
            cpu_percent = 0.0
            for key in ["CPUPerc", "CPU %"]:
                if key in data:
                    cpu_percent = float(data[key].replace("%", ""))
                    break

            # Memory (поддержка разных форматов)
            mem_usage_str = data.get("MemUsage", data.get("Mem Usage", "0MiB / 0MiB"))
            mem_parts = mem_usage_str.split("/")
            mem_usage = self._parse_size(mem_parts[0].strip())
            mem_limit = (
                self._parse_size(mem_parts[1].strip()) if len(mem_parts) > 1 else 0
            )

            mem_percent = 0.0
            for key in ["MemPerc", "Mem %"]:
                if key in data:
                    mem_percent = float(data[key].replace("%", ""))
                    break

            # Network (поддержка разных форматов)
            net_io_str = data.get("NetIO", data.get("Net I/O", "0B / 0B"))
            net_parts = net_io_str.split("/")
            net_rx = self._parse_size(net_parts[0].strip())
            net_tx = self._parse_size(net_parts[1].strip()) if len(net_parts) > 1 else 0

            # Block I/O (поддержка разных форматов)
            block_str = data.get("BlockIO", data.get("Block I/O", "0B / 0B"))
            block_parts = block_str.split("/")
            block_read = self._parse_size(block_parts[0].strip())
            block_write = (
                self._parse_size(block_parts[1].strip()) if len(block_parts) > 1 else 0
            )

            return {
                "cpu_percent": cpu_percent,
                "memory_usage_mb": mem_usage,
                "memory_limit_mb": mem_limit,
                "memory_percent": mem_percent,
                "network_rx_mb": net_rx,
                "network_tx_mb": net_tx,
                "block_read_mb": block_read,
                "block_write_mb": block_write,
            }
        except Exception as e:
            print(f"⚠️ Ошибка парсинга: {e}")
            return None

    def _parse_size(self, size_str: str) -> float:
        """Конвертирует строку размера (KiB, MiB, GiB) в MB."""
        size_str = size_str.strip()
        try:
            if "GiB" in size_str:
                return float(size_str.replace("GiB", "").strip()) * 1024
            elif "MiB" in size_str:
                return float(size_str.replace("MiB", "").strip())
            elif "KiB" in size_str:
                return float(size_str.replace("KiB", "").strip()) / 1024
            elif "GB" in size_str:
                return float(size_str.replace("GB", "").strip()) * 1000
            elif "MB" in size_str:
                return float(size_str.replace("MB", "").strip())
            elif "KB" in size_str:
                return float(size_str.replace("KB", "").strip()) / 1000
            elif "B" in size_str:
                return float(size_str.replace("B", "").strip()) / (1024 * 1024)
            else:
                return float(size_str)
        except ValueError:
            return 0.0

    def collect_metric(self):
        """Собирает одну метрику."""
        stats = self.get_stats()
        if stats:
            now = datetime.now()
            self.metrics["timestamps"].append(now.strftime("%H:%M:%S"))
            self.metrics["cpu_percent"].append(stats["cpu_percent"])
            self.metrics["memory_usage_mb"].append(stats["memory_usage_mb"])
            self.metrics["memory_limit_mb"].append(stats["memory_limit_mb"])
            self.metrics["memory_percent"].append(stats["memory_percent"])
            self.metrics["network_rx_mb"].append(stats["network_rx_mb"])
            self.metrics["network_tx_mb"].append(stats["network_tx_mb"])
            self.metrics["block_read_mb"].append(stats["block_read_mb"])
            self.metrics["block_write_mb"].append(stats["block_write_mb"])

            print(
                f"  [{now.strftime('%H:%M:%S')}] "
                f"CPU: {stats['cpu_percent']:.1f}% | "
                f"RAM: {stats['memory_usage_mb']:.0f}MB ({stats['memory_percent']:.1f}%) | "
                f"Net: ↓{stats['network_rx_mb']:.1f} ↑{stats['network_tx_mb']:.1f} MB"
            )

    def start_monitoring(self, duration_sec: int = 60, interval_sec: float = 2.0):
        """Запускает мониторинг на заданное время."""
        print(f"\n🔍 Мониторинг контейнера '{self.container_name}'...")
        print(f"⏱️ Длительность: {duration_sec} сек, интервал: {interval_sec} сек")
        print("-" * 70)

        if not self.check_container_running():
            print(f"❌ Контейнер '{self.container_name}' не запущен!")
            print("   Запустите: docker-compose up -d")
            return False

        self.running = True
        self.start_time = time.time()

        # Обработчик прерывания
        def signal_handler(sig, frame):
            print("\n⏹️ Остановка мониторинга...")
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)

        iterations = 0
        max_iterations = int(duration_sec / interval_sec)

        while self.running and iterations < max_iterations:
            self.collect_metric()
            iterations += 1
            time.sleep(interval_sec)

        print("-" * 70)
        print(f"✅ Собрано {len(self.metrics['timestamps'])} метрик")
        return True

    def generate_report(self, output_dir: str = "./profiling_results") -> str:
        """Генерирует HTML отчет."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Сохраняем JSON
        json_path = output_path / "docker_metrics.json"
        report_data = {
            "container": self.container_name,
            "start_time": self.start_time,
            "duration_sec": time.time() - self.start_time if self.start_time else 0,
            "metrics": self.metrics,
            "summary": self._calculate_summary(),
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        # Генерируем HTML
        html_path = output_path / "docker_monitoring.html"
        html = self._generate_html(report_data)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"\n📁 JSON данные: {json_path}")
        print(f"📁 HTML отчет: {html_path}")

        return str(html_path)

    def _calculate_summary(self) -> dict:
        """Вычисляет сводную статистику."""
        if not self.metrics["cpu_percent"]:
            return {}

        return {
            "cpu_avg": sum(self.metrics["cpu_percent"])
            / len(self.metrics["cpu_percent"]),
            "cpu_max": max(self.metrics["cpu_percent"]),
            "memory_avg": sum(self.metrics["memory_usage_mb"])
            / len(self.metrics["memory_usage_mb"]),
            "memory_max": max(self.metrics["memory_usage_mb"]),
            "memory_percent_avg": sum(self.metrics["memory_percent"])
            / len(self.metrics["memory_percent"]),
            "network_rx_total": self.metrics["network_rx_mb"][-1]
            if self.metrics["network_rx_mb"]
            else 0,
            "network_tx_total": self.metrics["network_tx_mb"][-1]
            if self.metrics["network_tx_mb"]
            else 0,
            "samples": len(self.metrics["timestamps"]),
        }

    def _generate_html(self, data: dict) -> str:
        """Генерирует красивый HTML отчет."""
        summary = data.get("summary", {})

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Мониторинг Docker - {self.container_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
            min-height: 100vh;
            padding: 40px 20px;
            color: #e0e0e0;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            font-size: 2.5rem;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .header p {{ color: #888; font-size: 1.1rem; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
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
            font-size: 1.3rem;
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
            font-size: 1.6rem;
            font-weight: bold;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stat-label {{ font-size: 0.85rem; color: #888; margin-top: 5px; }}
        .chart-container {{
            position: relative;
            height: 280px;
            margin-top: 15px;
        }}
        .full-width {{ grid-column: 1 / -1; }}
        .info-box {{
            background: rgba(0,217,255,0.05);
            border: 1px solid rgba(0,217,255,0.2);
            border-radius: 10px;
            padding: 15px;
            margin-top: 15px;
        }}
        .info-box p {{
            font-size: 0.9rem;
            color: #aaa;
            line-height: 1.6;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            margin: 3px;
        }}
        .badge-good {{ background: rgba(0,255,136,0.2); color: #00ff88; }}
        .badge-warning {{ background: rgba(255,206,86,0.2); color: #ffce56; }}
        .badge-danger {{ background: rgba(255,99,132,0.2); color: #ff6384; }}
        @media (max-width: 768px) {{
            .grid {{ grid-template-columns: 1fr; }}
            .stat-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐳 Мониторинг Docker Контейнера</h1>
            <p>Контейнер: <strong>{self.container_name}</strong> | 
               Длительность: {summary.get("samples", 0) * 2} сек | 
               Сэмплов: {summary.get("samples", 0)}</p>
        </div>

        <div class="grid">
            <!-- Summary Stats -->
            <div class="card">
                <h2>📊 Сводная статистика</h2>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-value">{summary.get("cpu_avg", 0):.1f}%</div>
                        <div class="stat-label">CPU (среднее)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary.get("cpu_max", 0):.1f}%</div>
                        <div class="stat-label">CPU (максимум)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary.get("memory_avg", 0):.0f} МБ</div>
                        <div class="stat-label">RAM (среднее)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary.get("memory_max", 0):.0f} МБ</div>
                        <div class="stat-label">RAM (максимум)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary.get("memory_percent_avg", 0):.1f}%</div>
                        <div class="stat-label">RAM (% от лимита)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary.get("network_rx_total", 0):.1f} МБ</div>
                        <div class="stat-label">Сеть (входящая)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{summary.get("network_tx_total", 0):.1f} МБ</div>
                        <div class="stat-label">Сеть (исходящая)</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">{data.get("duration_sec", 0):.0f} сек</div>
                        <div class="stat-label">Время мониторинга</div>
                    </div>
                </div>

                <div class="info-box">
                    <p>
                        <strong>💡 Рекомендации:</strong><br>
                        {"✅ Потребление памяти в норме" if summary.get("memory_percent_avg", 0) < 50 else "⚠️ Высокое потребление памяти" if summary.get("memory_percent_avg", 0) < 80 else "🔴 Критическое потребление памяти"}<br>
                        {"✅ CPU нагрузка низкая" if summary.get("cpu_avg", 0) < 30 else "⚠️ Средняя нагрузка CPU" if summary.get("cpu_avg", 0) < 70 else "🔴 Высокая нагрузка CPU"}
                    </p>
                </div>
            </div>

            <!-- CPU Chart -->
            <div class="card">
                <h2>📈 CPU Usage</h2>
                <div class="chart-container">
                    <canvas id="cpuChart"></canvas>
                </div>
            </div>

            <!-- Memory Chart -->
            <div class="card">
                <h2>💾 Memory Usage</h2>
                <div class="chart-container">
                    <canvas id="memoryChart"></canvas>
                </div>
            </div>

            <!-- Network Chart -->
            <div class="card full-width">
                <h2>🌐 Network Traffic</h2>
                <div class="chart-container">
                    <canvas id="networkChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Status Badges -->
        <div class="card">
            <h2>🏷️ Статус системы</h2>
            <div style="margin-top: 15px;">
                {self._generate_badge(summary.get("cpu_avg", 0), "CPU", [30, 70])}
                {self._generate_badge(summary.get("memory_percent_avg", 0), "RAM", [50, 80])}
                {self._generate_badge(summary.get("memory_max", 0) / 1024, "RAM (GB)", [1, 2])}
                <span class="badge badge-good">Streamlit готов</span>
            </div>
        </div>
    </div>

    <script>
        const timestamps = {json.dumps(data["metrics"]["timestamps"])};
        
        // CPU Chart
        new Chart(document.getElementById('cpuChart'), {{
            type: 'line',
            data: {{
                labels: timestamps,
                datasets: [{{
                    label: 'CPU %',
                    data: {json.dumps(data["metrics"]["cpu_percent"])},
                    borderColor: 'rgba(0, 217, 255, 1)',
                    backgroundColor: 'rgba(0, 217, 255, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        ticks: {{ color: '#888' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#888', maxTicksLimit: 10 }}
                    }}
                }}
            }}
        }});

        // Memory Chart
        new Chart(document.getElementById('memoryChart'), {{
            type: 'line',
            data: {{
                labels: timestamps,
                datasets: [{{
                    label: 'RAM (МБ)',
                    data: {json.dumps(data["metrics"]["memory_usage_mb"])},
                    borderColor: 'rgba(0, 255, 136, 1)',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        ticks: {{ color: '#888' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#888', maxTicksLimit: 10 }}
                    }}
                }}
            }}
        }});

        // Network Chart
        new Chart(document.getElementById('networkChart'), {{
            type: 'line',
            data: {{
                labels: timestamps,
                datasets: [
                    {{
                        label: 'Входящий трафик (МБ)',
                        data: {json.dumps(data["metrics"]["network_rx_mb"])},
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }},
                    {{
                        label: 'Исходящий трафик (МБ)',
                        data: {json.dumps(data["metrics"]["network_tx_mb"])},
                        borderColor: 'rgba(54, 162, 235, 1)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                        labels: {{ color: '#e0e0e0' }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        ticks: {{ color: '#888' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#888', maxTicksLimit: 10 }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
        return html

    def _generate_badge(self, value: float, label: str, thresholds: list) -> str:
        """Генерирует HTML бейдж."""
        if value < thresholds[0]:
            css_class = "badge-good"
            text = f"✅ {label}: OK"
        elif value < thresholds[1]:
            css_class = "badge-warning"
            text = f"⚠️ {label}: Warning"
        else:
            css_class = "badge-danger"
            text = f"🔴 {label}: Critical"

        return f'<span class="badge {css_class}">{text}</span>'


def main():
    """Запуск мониторинга."""
    import argparse

    parser = argparse.ArgumentParser(description="Мониторинг Docker контейнера")
    parser.add_argument(
        "--container",
        default="smarthandyman_app",
        help="Имя контейнера (по умолчанию: smarthandyman_app)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Длительность мониторинга в секундах (по умолчанию: 60)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Интервал сбора метрик в секундах (по умолчанию: 2.0)",
    )
    parser.add_argument(
        "--output",
        default="./profiling_results",
        help="Директория для отчета (по умолчанию: ./profiling_results)",
    )

    args = parser.parse_args()

    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  МОНИТОРИНГ DOCKER КОНТЕЙНЕРА                                ║")
    print("║  SmartHandyman Application                                   ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    monitor = DockerMonitor(args.container)

    if monitor.start_monitoring(duration_sec=args.duration, interval_sec=args.interval):
        monitor.generate_report(args.output)
        print("\n✅ Мониторинг завершен!")
    else:
        print("\n❌ Не удалось запустить мониторинг")
        sys.exit(1)


if __name__ == "__main__":
    main()
