import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_BASE_URL = os.getenv("CLAUDE_BASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Provider selection: "claude" or "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude").lower()

# Model settings for Claude
CLAUDE_VISION_MODEL = "claude-sonnet-4-5-20250514"
CLAUDE_TEXT_MODEL = "claude-haiku-4-5-20251001"

# Model settings for OpenAI
OPENAI_VISION_MODEL = "gpt-5-nano"
OPENAI_TEXT_MODEL = "gpt-5-nano"

if LLM_PROVIDER == "openai":
    VISION_MODEL = OPENAI_VISION_MODEL
    TEXT_MODEL = OPENAI_TEXT_MODEL
    ACTIVE_API_KEY = OPENAI_API_KEY
else:
    VISION_MODEL = CLAUDE_VISION_MODEL
    TEXT_MODEL = CLAUDE_TEXT_MODEL
    ACTIVE_API_KEY = CLAUDE_API_KEY

# System prompt for LLMs
SYSTEM_PROMPT = """Ты - экспертная система для диагностики и ремонта бытовых устройств. 
Твоя задача - помогать пользователям с ремонтом техники, сантехники, электрики и других бытовых проблем.
Отвечай на русском языке, давай конкретные практические инструкции.
Всегда следуй формату, указанному в запросе пользователя."""

# Safety keywords for dangerous repairs
DANGER_KEYWORDS = [
    "электричество",
    "электрический",
    "провод",
    "розетка",
    "щиток",
    "автомат",
    "газ",
    "газовый",
    "утечка",
    "запах газа",
    "котел",
    "колонка",
    "высокое напряжение",
    "220в",
    "380в",
    "электропроводка",
    "electricity",
    "electrical",
    "wire",
    "socket",
    "gas",
    "voltage",
]

VISION_TEMPERATURE = 0.3
TEXT_TEMPERATURE = 0.7
DIAGNOSTIC_TEMPERATURE = 0.5
VISION_MAX_TOKENS = 4096
TEXT_MAX_TOKENS = 4096
DIAGNOSTIC_MAX_TOKENS = 4096

# RAG settings
CHROMA_DB_PATH = "./rag/rag_store"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
