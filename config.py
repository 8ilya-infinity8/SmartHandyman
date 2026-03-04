"""Configuration settings for the repair assistant."""

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
CLAUDE_VISION_MODEL = "claude-haiku-4-5-20251001"
CLAUDE_TEXT_MODEL = "claude-haiku-4-5-20251001"

# Model settings for OpenAI
OPENAI_VISION_MODEL = "gpt-4o"
OPENAI_TEXT_MODEL = "gpt-4o-mini"

# Active models based on provider
if LLM_PROVIDER == "claude":
    VISION_MODEL = CLAUDE_VISION_MODEL
    TEXT_MODEL = CLAUDE_TEXT_MODEL
    ACTIVE_API_KEY = CLAUDE_API_KEY
elif LLM_PROVIDER == "openai":
    VISION_MODEL = OPENAI_VISION_MODEL
    TEXT_MODEL = OPENAI_TEXT_MODEL
    ACTIVE_API_KEY = OPENAI_API_KEY
else:
    # Default to Claude if invalid provider
    VISION_MODEL = CLAUDE_VISION_MODEL
    TEXT_MODEL = CLAUDE_TEXT_MODEL
    ACTIVE_API_KEY = CLAUDE_API_KEY

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

# RAG settings
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
