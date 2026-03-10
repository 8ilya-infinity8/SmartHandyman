FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
# Общие агенты и конфиги, которые использует backend-ассистент
COPY config.py llm_client.py diagnostic_agent.py instruction_generator.py safety_checker.py shopping_agent.py vision_analyzer.py ./ 
COPY rag ./rag
RUN python -m rag.index_corpus
# Делаем рабочей директорией корень backend, как при локальном запуске,
# чтобы пакет "app" был на верхнем уровне импорта.
WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

