"""Tests for the Enterprise RAG AI Chatbot.

Retrieval, the ask endpoint, ingestion, and validation. All answers in
the default configuration come from the local extractive generator over
synthetic seeded documents; no Azure OpenAI endpoint is used.
"""
from fastapi.testclient import TestClient

from app.main import app
from app.rag import RagService

client = TestClient(app)


def test_retrieval_returns_the_billing_document():
    service = RagService()
    results = service.retrieve("How do I change my payment method?", top_k=3)
    assert len(results) == 3
    top_chunk, top_score = results[0]
    assert top_chunk.doc_id == "DOC-BILLING-001"
    assert top_score > 0.1
    assert "payment" in top_chunk.text.lower()


def test_retrieval_returns_the_returns_document_for_refund_question():
    service = RagService()
    results = service.retrieve("How long do refunds take after a return?", top_k=3)
    assert results[0][0].doc_id == "DOC-RETURNS-001"


def test_ask_endpoint_returns_answer_with_sources():
    response = client.post(
        "/api/v1/chat/ask",
        json={"question": "How do I reset my password?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "local-extractive-v1"
    assert "password" in data["answer"].lower()
    assert len(data["sources"]) >= 1
    assert data["sources"][0]["doc_id"] == "DOC-ACCOUNT-001"
    assert "latency_ms" in data


def test_ask_endpoint_rejects_short_question():
    response = client.post("/api/v1/chat/ask", json={"question": "hi"})
    assert response.status_code == 422


def test_ingest_adds_a_document_and_it_is_retrievable():
    response = client.post(
        "/api/v1/documents",
        json={
            "title": "Test document about store opening hours",
            "category": "test",
            "text": (
                "The downtown store opens at nine in the morning and closes "
                "at nine in the evening on weekdays, and from ten in the "
                "morning to six in the evening on Sundays."
            ),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["chunks"] >= 1
    ask = client.post(
        "/api/v1/chat/ask",
        json={"question": "What time does the downtown store open?"},
    )
    assert ask.status_code == 200
    assert any(
        source["doc_id"] == data["id"] for source in ask.json()["sources"]
    )


def test_stats_and_documents_endpoints():
    stats = client.get("/api/v1/stats")
    assert stats.status_code == 200
    assert stats.json()["documents"] >= 8
    assert stats.json()["chunks"] >= 8
    assert stats.json()["embedding_model"] == "tfidf-local-v1"
    docs = client.get("/api/v1/documents")
    assert docs.status_code == 200
    titles = [doc["title"] for doc in docs.json()["documents"]]
    assert "Returns and refunds policy" in titles
