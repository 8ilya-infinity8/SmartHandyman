"""FAISS retriever для SmartHandyman.

Загружает индекс и модель один раз за весь процесс (синглтон),
чтобы не жрать ресурсы при каждом рендере Streamlit.

Использует лёгкую модель из config.py вместо тяжёлой e5-large.
Интерфейс: search(query, k, min_score) — совместим с instruction_generator.py.
"""

import sys
import os

# Добавить корень проекта (на два уровня вверх от текущего файла)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pickle
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np

from config import CHROMA_DB_PATH, EMBEDDING_MODEL

INDEX_DIR = Path(CHROMA_DB_PATH) if CHROMA_DB_PATH else Path("rag/rag_store")

# ─── Синглтон ────────────────────────────────────────────────────────────────
# Модель и индекс живут здесь всё время работы процесса.
# Streamlit может рендерить страницу 100 раз — загрузка произойдёт один раз.
_retriever_instance: Optional["Retriever"] = None


def load_retriever() -> "Retriever":
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance


# ─── Класс ───────────────────────────────────────────────────────────────────


class Retriever:
    def __init__(self):
        index_path = INDEX_DIR / "index.faiss"
        chunks_path = INDEX_DIR / "chunks.pkl"
        meta_path = INDEX_DIR / "metadata.pkl"

        if not index_path.exists():
            print(f"[Retriever] index.faiss не найден в {INDEX_DIR} — RAG отключён")
            self._ready = False
            return

        # Грузим FAISS (только faiss-cpu, torch не нужен)
        import faiss

        self._index = faiss.read_index(str(index_path))

        with open(chunks_path, "rb") as f:
            self._chunks: List[str] = pickle.load(f)
        with open(meta_path, "rb") as f:
            self._meta: List[dict] = pickle.load(f)

        # Лёгкая многоязычная модель (~120 МБ против ~1.3 ГБ у e5-large)
        # Имя берём из config.py: paraphrase-multilingual-MiniLM-L12-v2
        from sentence_transformers import SentenceTransformer

        model_name = EMBEDDING_MODEL.replace("sentence-transformers/", "")
        self._model = SentenceTransformer(model_name)

        self._ready = True
        print(
            f"[Retriever] Загружено {self._index.ntotal} векторов, модель: {model_name}"
        )

    # ─────────────────────────────────────────────────────────────────────────

    def search(self, query: str, k: int = 5, min_score: float = 0.0) -> List[Dict]:
        """Возвращает до k релевантных чанков. Пустой список если RAG недоступен."""
        if not self._ready:
            return []

        # Кодируем запрос (без префикса "query:" — MiniLM не требует)
        q_emb = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)

        scores, indices = self._index.search(q_emb, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            if float(score) < min_score:
                continue
            text = self._chunks[idx]
            # Убираем префикс "passage: " если он есть (от e5-модели)
            if text.startswith("passage: "):
                text = text[9:]
            meta = self._meta[idx] if idx < len(self._meta) else {}
            results.append(
                {
                    "score": round(float(score), 4),
                    "text": text,
                    "source": meta.get("source"),
                    "title": meta.get("title"),
                    "provider": meta.get("provider"),
                }
            )

        return results
