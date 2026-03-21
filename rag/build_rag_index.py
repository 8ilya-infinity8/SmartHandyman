"""
build_rag_index.py — сбор базы знаний для SmartHandyman.

Запуск из Docker-контейнера (Python уже с установленными зависимостями):
    python /app/rag/build_rag_index.py
"""

from __future__ import annotations
import re
import time
import pickle
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
import requests
from bs4 import BeautifulSoup
from tqdm.auto import tqdm
import faiss
from sentence_transformers import SentenceTransformer

# ───────────────────── Пути ─────────────────────

PROJECT_ROOT = Path(__file__).parent
RAG_DIR = PROJECT_ROOT / "rag_store"
RAG_DIR.mkdir(exist_ok=True)

INDEX_PATH = RAG_DIR / "index.faiss"
CHUNKS_PATH = RAG_DIR / "chunks.pkl"
METADATA_PATH = RAG_DIR / "metadata.pkl"

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ───────────────────── Функции для источников ─────────────────────

# iFixit
IFIXIT_BASE = "https://www.ifixit.com/api/2.0"
IFIXIT_HEADERS = {"User-Agent": "RAG-Handyman/cli-2.0"}


def ifixit_get(endpoint: str, params: dict | None = None) -> Optional[dict]:
    try:
        resp = requests.get(
            f"{IFIXIT_BASE}{endpoint}",
            headers=IFIXIT_HEADERS,
            params=params,
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[iFixit] {endpoint}: {e}")
        return None


def get_ifixit_guides(category: str) -> List[dict]:
    data = ifixit_get(f"/wikis/CATEGORY/{category}")
    if not data:
        return []
    guides = data.get("guides", [])
    if not guides:
        for cl in data.get("category_lists", []):
            guides.extend(cl.get("guides", []))
    return guides


def get_ifixit_guide(guide_id: int) -> Optional[dict]:
    return ifixit_get(f"/guides/{guide_id}")


def parse_ifixit_guide(guide: dict) -> str:
    parts: List[str] = []
    title = guide.get("title", "")
    if title:
        parts.append(f"Guide: {title}")

    intro = guide.get("introduction_rendered") or guide.get("introduction", "")
    if intro:
        parts.append(BeautifulSoup(intro, "html.parser").get_text(" ").strip())

    for step in guide.get("steps", []):
        step_title = step.get("title", "")
        if step_title:
            parts.append(f"Step {step.get('orderby', '')}: {step_title}")
        for line in step.get("lines", []):
            text = line.get("text", "").strip()
            if text:
                text = re.sub(r"\[([^\]]*?)\|?[^\]]*?\]", r"\1", text)
                text = re.sub(r"['\"][\"']{0,2}", "", text)
                parts.append(text)
    return "\n".join(filter(None, parts))


def fetch_ifixit_category(
    category: str, delay: float = 0.7, max_guides: int | None = None
) -> List[Dict]:
    guides_meta = get_ifixit_guides(category)
    if not guides_meta:
        print(f"[iFixit] пустая категория: {category}")
        return []

    results: List[Dict] = []
    iterable = guides_meta if max_guides is None else guides_meta[:max_guides]
    for meta in tqdm(iterable, desc=f"iFixit [{category}]"):
        guide_id = meta.get("guideid")
        if not guide_id:
            continue
        guide = get_ifixit_guide(guide_id)
        if not guide:
            continue
        text = parse_ifixit_guide(guide)
        if text:
            results.append(
                {
                    "text": text,
                    "source": f"https://www.ifixit.com/Guide/{guide_id}",
                    "title": guide.get("title", ""),
                    "provider": "ifixit",
                }
            )
        time.sleep(delay)
    print(f"[iFixit] {category}: {len(results)} гайдов")
    return results


# ───────────────────── Чанкование ─────────────────────


def chunk_text(
    text: str, chunk_size: int = 400, overlap: int = 80, min_chunk_words: int = 30
) -> List[str]:
    words = text.split()
    if not words:
        return []
    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("overlap должен быть меньше chunk_size")
    chunks: List[str] = []
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        if len(chunk_words) < min_chunk_words and chunks:
            chunks[-1] += " " + " ".join(chunk_words)
            break
        chunks.append(" ".join(chunk_words))
    return chunks


def documents_to_chunks(
    documents: List[Dict], chunk_size: int = 400, overlap: int = 80
) -> tuple[list[str], list[dict]]:
    all_chunks: list[str] = []
    metadata: list[dict] = []
    for doc in documents:
        for chunk in chunk_text(doc["text"], chunk_size=chunk_size, overlap=overlap):
            all_chunks.append(chunk)
            metadata.append(
                {
                    "source": doc["source"],
                    "title": doc.get("title", ""),
                    "provider": doc.get("provider", "unknown"),
                }
            )
    print(f"Итого чанков: {len(all_chunks)}")
    return all_chunks, metadata


# ───────────────────── Main ─────────────────────


def main() -> None:
    print("PROJECT_ROOT:", PROJECT_ROOT)
    print("RAG_DIR     :", RAG_DIR)
    print("Модель      :", EMBEDDING_MODEL)

    all_documents: List[Dict] = []

    # Для примера возьмем только несколько категорий iFixit
    ifixit_categories = ["Washing_Machine", "Dryer", "Dishwasher"]

    for category in ifixit_categories:
        all_documents.extend(fetch_ifixit_category(category, delay=0.5))

    if not all_documents:
        print("Документов нет — ничего не сохраняю.")
        return

    all_chunks, metadata = documents_to_chunks(
        all_documents, chunk_size=400, overlap=80
    )

    print("\nСчитаю эмбеддинги...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = model.encode(
        all_chunks,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(INDEX_PATH))
    with CHUNKS_PATH.open("wb") as f:
        pickle.dump(all_chunks, f)
    with METADATA_PATH.open("wb") as f:
        pickle.dump(metadata, f)

    print("Готово! Индекс сохранен в", INDEX_PATH)


if __name__ == "__main__":
    main()
