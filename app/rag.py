"""RAG service: chunk, embed, retrieve, generate.

Pipeline, in the LangChain style:
  documents -> RecursiveCharacterTextSplitter -> embeddings
  -> FAISS vector store -> top-k retrieval -> answer generation

Generation tries Azure OpenAI GPT-4 first, only when it is configured.
Otherwise the local extractive generator answers from the retrieved
chunks. The response always says which model produced the answer, and
always lists the retrieved chunks as sources with their scores.
"""
import re
import time
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import settings
from .documents import SEED_DOCUMENTS
from .embeddings import AzureEmbeddings, TfidfEmbeddings, tokenize
from .vector_store import Chunk, FaissVectorStore

LOCAL_MODEL = "local-extractive-v1"
AZURE_MODEL = "azure-openai-gpt-4"
MIN_SCORE = 0.05
_SENTENCE = re.compile(r"(?<=[.!?])\s+")


class RagService:
    def __init__(self) -> None:
        self.documents: list[dict] = [dict(doc) for doc in SEED_DOCUMENTS]
        if (
            settings.azure_configured
            and settings.azure_openai_embedding_deployment
        ):
            self.embedder = AzureEmbeddings(
                endpoint=settings.azure_openai_endpoint or "",
                api_key=settings.azure_openai_api_key or "",
                deployment=settings.azure_openai_embedding_deployment,
                api_version=settings.azure_openai_api_version,
            )
        else:
            self.embedder = TfidfEmbeddings()
        self.store = FaissVectorStore()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._rebuild_index()

    # -- indexing -----------------------------------------------------
    def _chunk_documents(self) -> list[Chunk]:
        chunks: list[Chunk] = []
        for doc in self.documents:
            parts = self.splitter.split_text(doc["text"])
            for i, part in enumerate(parts):
                chunks.append(
                    Chunk(
                        doc_id=doc["id"],
                        title=doc["title"],
                        category=doc["category"],
                        # The splitter drops the ". " separator at chunk
                        # boundaries, leaving a leading ". " on some chunks.
                        text=part.strip().lstrip(". "),
                        chunk_index=i,
                    )
                )
        return chunks

    def _rebuild_index(self) -> None:
        chunks = self._chunk_documents()
        texts = [chunk.text for chunk in chunks]
        if hasattr(self.embedder, "fit"):
            self.embedder.fit(texts)
        vectors = self.embedder.embed(texts)
        self.store.build(chunks, vectors)
        # IDF over chunks, for reranking: a rare content word ("refund")
        # is worth more than a common verb ("take") when both match once.
        import math

        doc_freq: dict[str, int] = {}
        for text in texts:
            for token in set(tokenize(text)):
                doc_freq[token] = doc_freq.get(token, 0) + 1
        n = max(len(texts), 1)
        self._idf = {
            token: math.log((n + 1) / (freq + 1)) + 1.0
            for token, freq in doc_freq.items()
        }

    # -- public API ---------------------------------------------------
    def list_documents(self) -> list[dict]:
        return [
            {
                "id": doc["id"],
                "title": doc["title"],
                "category": doc["category"],
                "chars": len(doc["text"]),
            }
            for doc in self.documents
        ]

    def stats(self) -> dict:
        return {
            "documents": len(self.documents),
            "chunks": len(self.store),
            "embedding_model": self.embedder.name,
            "vector_store": "faiss",
            "azure_configured": settings.azure_configured,
            "generation_model": AZURE_MODEL if settings.azure_configured else LOCAL_MODEL,
        }

    def ingest(self, title: str, category: str, text: str) -> dict:
        doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
        self.documents.append(
            {"id": doc_id, "title": title, "category": category, "text": text}
        )
        self._rebuild_index()
        chunks = [c for c in self.store.chunks if c.doc_id == doc_id]
        return {
            "id": doc_id,
            "title": title,
            "category": category,
            "chunks": len(chunks),
            "total_documents": len(self.documents),
            "total_chunks": len(self.store),
        }

    def retrieve(self, question: str, top_k: int) -> list[tuple[Chunk, float]]:
        query_vector = self.embedder.embed([question])
        # Fetch more candidates than needed, then rerank: a chunk that
        # shares more distinct content words with the question wins over
        # one that only scored well on TF-IDF cosine. This stops a chunk
        # like "Restocking fees do not apply" outranking the refund-timing
        # chunk for "How long do refunds take?".
        candidates = self.store.search(query_vector[0], max(top_k * 3, 10))
        query_tokens = set(tokenize(question))

        def rerank_key(item: tuple[Chunk, float]) -> tuple[float, int, float]:
            chunk, score = item
            matched = query_tokens & set(tokenize(chunk.text))
            idf_weight = sum(self._idf.get(token, 0.0) for token in matched)
            return (idf_weight, len(matched), score)

        candidates.sort(key=rerank_key, reverse=True)
        return candidates[:top_k]

    def ask(self, question: str, top_k: int | None = None) -> dict:
        started = time.monotonic()
        k = top_k or settings.default_top_k
        results = self.retrieve(question, k)
        # Drop chunks with zero similarity: they matched nothing and only
        # add noise to the citations.
        sources = [
            {**chunk.to_dict(), "score": round(score, 4)}
            for chunk, score in results
            if score > 0
        ]
        if not results or results[0][1] < MIN_SCORE:
            answer = (
                "I couldn't find an answer to that in the support "
                "documents I have. Try asking about billing, your "
                "account, orders, returns, device setup, warranty, "
                "plans, or account security."
            )
            model = LOCAL_MODEL
        elif settings.azure_configured:
            answer, model = self._generate_with_azure(question, results)
            if answer is None:
                answer = self._generate_locally(question, results)
                model = LOCAL_MODEL
        else:
            answer = self._generate_locally(question, results)
            model = LOCAL_MODEL
        latency_ms = round((time.monotonic() - started) * 1000, 1)
        return {
            "question": question,
            "answer": answer,
            "model": model,
            "sources": sources,
            "latency_ms": latency_ms,
        }

    # -- generation ---------------------------------------------------
    def _generate_locally(self, question: str, results: list[tuple[Chunk, float]]) -> str:
        # Answer only from the top-ranked chunk: pulling sentences from
        # lower-ranked chunks mixed in unrelated advice (for example a
        # security sentence in an answer about payment methods).
        query_tokens = set(tokenize(question))
        top_chunk = results[0][0]
        scored: list[tuple[int, str]] = []
        for sentence in _SENTENCE.split(top_chunk.text):
            sentence = sentence.strip()
            if not sentence:
                continue
            overlap = len(query_tokens & set(tokenize(sentence)))
            scored.append((overlap, sentence))
        scored.sort(key=lambda item: item[0], reverse=True)
        picked = [sentence for overlap, sentence in scored[:2] if overlap > 0]
        if not picked:
            picked = [scored[0][1]] if scored else [top_chunk.text]
        # The text splitter drops the ". " separator at chunk boundaries,
        # so a sentence can arrive without its final period. Restore it.
        fixed = [
            sentence if sentence.endswith((".", "!", "?")) else sentence + "."
            for sentence in picked
        ]
        return " ".join(fixed)

    def _generate_with_azure(
        self, question: str, results: list[tuple[Chunk, float]]
    ) -> tuple[str | None, str]:
        try:
            from langchain_core.messages import HumanMessage
            from langchain_openai import AzureChatOpenAI

            context = "\n\n".join(
                f"[{chunk.title}] {chunk.text}" for chunk, _ in results
            )
            llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                azure_deployment=settings.azure_openai_deployment,
                api_version=settings.azure_openai_api_version,
                temperature=0,
            )
            prompt = (
                "You are an enterprise customer-support assistant. "
                "Answer the question using ONLY the support documents "
                "below. If the documents do not contain the answer, say "
                "you could not find it. Keep the answer to two or three "
                "sentences.\n\nDocuments:\n" + context +
                "\n\nQuestion: " + question
            )
            reply = llm.invoke([HumanMessage(content=prompt)])
            return str(reply.content), AZURE_MODEL
        except Exception:
            return None, LOCAL_MODEL
