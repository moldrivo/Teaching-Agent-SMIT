import hashlib
import math
import os
import re
import time
from typing import List

import chromadb

from app.config import settings

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "and", "or", "but", "if", "then", "else", "to", "of", "in", "on",
    "for", "with", "at", "by", "from", "as", "that", "this", "these",
    "those", "it", "its", "we", "you", "they", "he", "she", "i", "me",
    "my", "your", "our", "not", "can", "could", "will", "would", "should",
    "do", "does", "did", "have", "has", "had", "how", "what", "why", "about",
}


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9_]+", text.lower())
    return [w for w in words if w not in STOPWORDS]


def _stable_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def embed(text: str, dim: int = 64) -> List[float]:
    """Deterministic hashing embedding (no external model required).

    Swap for OpenAI embeddings / sentence-transformers when you want semantic
    quality — keep the same signature so retrieval code stays unchanged.
    """
    vec = [0.0] * dim
    for token in tokenize(text):
        vec[_stable_hash(token) % dim] += 1.0
    if not tokenize(text):
        vec[0] = 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class RAG:
    """Minimal RAG layer over ChromaDB (cosine, persistent)."""

    def __init__(self):
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self._client.get_or_create_collection(
            name="teaching_docs", metadata={"hnsw:space": "cosine"}
        )

    def ingest(self, documents: List[str], source: str = "generic") -> int:
        ids, metas = [], []
        for i, doc in enumerate(documents):
            uid = f"{source}-{int(time.time() * 1000)}-{i}"
            ids.append(uid)
            metas.append({"source": source})
        self.collection.add(
            ids=ids,
            embeddings=[embed(d) for d in documents],
            metadatas=metas,
            documents=documents,
        )
        return len(documents)

    def retrieve(self, query: str, k: int = 3) -> List[str]:
        if self.collection.count() == 0:
            return []
        result = self.collection.query(
            query_embeddings=[embed(query)],
            n_results=min(k, self.collection.count()),
        )
        return result.get("documents", [[]])[0]

    def count(self) -> int:
        return self.collection.count()
