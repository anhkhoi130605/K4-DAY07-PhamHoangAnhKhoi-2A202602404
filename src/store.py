from __future__ import annotations

import math
from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document."""
        self._next_index += 1
        record_id = getattr(doc, "id", None) or f"chunk_{self._next_index}"
        content = getattr(doc, "content", getattr(doc, "text", str(doc)))
        metadata = getattr(doc, "metadata", {}) or {}
        embedding = self._embedding_fn(content)

        return {
            "id": str(record_id),
            "content": content,
            "metadata": dict(metadata),
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records."""
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        norm_q = math.sqrt(_dot(query_embedding, query_embedding))

        scored_records: list[tuple[float, dict[str, Any]]] = []
        for rec in records:
            doc_emb = rec["embedding"]
            norm_d = math.sqrt(_dot(doc_emb, doc_emb))

            score = 0.0
            if norm_q > 0.0 and norm_d > 0.0:
                score = _dot(query_embedding, doc_emb) / (norm_q * norm_d)

            item = dict(rec)
            item["score"] = float(score)
            scored_records.append((score, item))

        scored_records.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_records[:top_k]]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma and self._collection is not None:
            ids = [r["id"] for r in records]
            documents = [r["content"] for r in records]
            embeddings = [r["embedding"] for r in records]
            metadatas = [r["metadata"] for r in records]
            self._collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )

        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        return self.search_with_filter(query=query, top_k=top_k, metadata_filter=None)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict | None = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter:
            candidate_records = [
                rec
                for rec in self._store
                if all(rec.get("metadata", {}).get(k) == v for k, v in metadata_filter.items())
            ]
        else:
            candidate_records = self._store

        return self._search_records(query, candidate_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        to_delete = [
            r["id"]
            for r in self._store
            if r.get("metadata", {}).get("doc_id") == doc_id or r.get("id") == doc_id
        ]

        if not to_delete:
            return False

        if self._use_chroma and self._collection is not None:
            try:
                self._collection.delete(ids=to_delete)
            except Exception:
                pass

        self._store = [
            r
            for r in self._store
            if r.get("metadata", {}).get("doc_id") != doc_id and r.get("id") != doc_id
        ]
        return True