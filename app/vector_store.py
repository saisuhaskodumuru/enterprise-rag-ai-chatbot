"""FAISS vector store over the chunked documents.

The store holds the chunk text plus the document it came from, so every
retrieved chunk can be cited. FAISS does the nearest-neighbour search
(IndexFlatIP on L2-normalised vectors, which is cosine similarity);
the embeddings themselves come from ``app.embeddings``.
"""
import faiss
import numpy as np


class Chunk:
    def __init__(self, doc_id: str, title: str, category: str, text: str, chunk_index: int):
        self.doc_id = doc_id
        self.title = title
        self.category = category
        self.text = text
        self.chunk_index = chunk_index

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "category": self.category,
            "text": self.text,
            "chunk_index": self.chunk_index,
        }


class FaissVectorStore:
    def __init__(self) -> None:
        self.chunks: list[Chunk] = []
        self.index: faiss.IndexFlatIP | None = None

    def build(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        self.chunks = list(chunks)
        if len(chunks) == 0:
            self.index = None
            return
        dimension = int(vectors.shape[1])
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(np.ascontiguousarray(vectors, dtype=np.float32))

    def search(self, query_vector: np.ndarray, top_k: int) -> list[tuple[Chunk, float]]:
        if self.index is None or len(self.chunks) == 0:
            return []
        vector = np.ascontiguousarray(query_vector.reshape(1, -1), dtype=np.float32)
        k = min(top_k, len(self.chunks))
        scores, ids = self.index.search(vector, k)
        results: list[tuple[Chunk, float]] = []
        for chunk_id, score in zip(ids[0], scores[0]):
            if int(chunk_id) < 0:
                continue
            results.append((self.chunks[int(chunk_id)], float(score)))
        return results

    def __len__(self) -> int:
        return len(self.chunks)
