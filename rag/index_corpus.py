"""Пересборка FAISS индекса из существующего chunks.pkl.

Не нужен data_docs.pkl — берём чанки как есть и пересчитываем эмбеддинги
моделью MiniLM (лёгкая, ~120 МБ, совместима с config.py).

Запуск:
    python -m rag.index_corpus
"""

import pickle
from pathlib import Path

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from config import CHROMA_DB_PATH

RAG_DIR = Path(CHROMA_DB_PATH) if CHROMA_DB_PATH else Path("rag/rag_store")
MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def main():
    print("Загружаю chunks.pkl и metadata.pkl...")
    with open(RAG_DIR / "chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    with open(RAG_DIR / "metadata.pkl", "rb") as f:
        meta = pickle.load(f)
    print(f"  {len(chunks)} чанков")

    # Убираем префикс "passage: " — MiniLM его не нужен
    clean = [c[9:] if c.startswith("passage: ") else c for c in chunks]

    print(f"Загружаю модель {MODEL}...")
    model = SentenceTransformer(MODEL)

    print("Считаю эмбеддинги (займёт 1-3 минуты)...")
    embeddings = model.encode(
        clean,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    print("Строю индекс FAISS...")
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    # Сохраняем — перезаписываем старые файлы
    faiss.write_index(index, str(RAG_DIR / "index.faiss"))
    # Сохраняем чанки уже без префикса
    with open(RAG_DIR / "chunks.pkl", "wb") as f:
        pickle.dump(clean, f)
    with open(RAG_DIR / "metadata.pkl", "wb") as f:
        pickle.dump(meta, f)

    print(f"\nГотово! {index.ntotal} векторов в {RAG_DIR}/")


if __name__ == "__main__":
    main()
