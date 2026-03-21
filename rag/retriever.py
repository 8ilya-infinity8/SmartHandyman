"""FAISS retriever для SmartHandyman"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from config import EMBEDDING_MODEL

# Всегда абсолютный путь
BASE_DIR = Path(__file__).resolve().parent
INDEX_DIR = BASE_DIR / "rag_store"
print("Looking for index at:", INDEX_DIR / "index.faiss")

# Синглтон
_retriever_instance: Optional["Retriever"] = None


def load_retriever() -> "Retriever":
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance


class Retriever:
    def __init__(self):
        index_path = INDEX_DIR / "index.faiss"
        chunks_path = INDEX_DIR / "chunks.pkl"
        meta_path = INDEX_DIR / "metadata.pkl"

        if not index_path.exists():
            print(f"[Retriever] index.faiss не найден в {INDEX_DIR} — RAG отключён")
            self._ready = False
            return

        import faiss
        from sentence_transformers import SentenceTransformer

        self._index = faiss.read_index(str(index_path))

        with open(chunks_path, "rb") as f:
            self._chunks: List[str] = pickle.load(f)
        with open(meta_path, "rb") as f:
            self._meta: List[dict] = pickle.load(f)

        model_name = EMBEDDING_MODEL.replace("sentence-transformers/", "")
        self._model = SentenceTransformer(model_name)

        self._ready = True
        print(
            f"[Retriever] Загружено {self._index.ntotal} векторов, модель: {model_name}"
        )

    def search(self, query: str, k: int = 5, min_score: float = 0.0) -> List[Dict]:
        if not getattr(self, "_ready", False):
            return []

        q_emb = self._model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)

        scores, indices = self._index.search(q_emb, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or float(score) < min_score:
                continue
            text = self._chunks[idx]
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
