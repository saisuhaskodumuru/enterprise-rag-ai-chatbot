"""FastAPI app for the Enterprise RAG AI Chatbot demo."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .config import settings
from .rag import AZURE_MODEL, LOCAL_MODEL, RagService

app = FastAPI(
    title="Enterprise RAG AI Chatbot",
    description=(
        "Document-aware customer-support chatbot. Retrieval uses LangChain "
        "chunking and a FAISS vector store; answers come from Azure OpenAI "
        "GPT-4 when configured, otherwise from a local extractive generator."
    ),
    version="1.0.0",
)
service = RagService()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=10)


class IngestRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    category: str = Field(..., min_length=2, max_length=50)
    text: str = Field(..., min_length=20, max_length=20000)


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "azure_configured": settings.azure_configured}


@app.get("/api/v1/stats")
def stats():
    return service.stats()


@app.get("/api/v1/documents")
def list_documents():
    return {"documents": service.list_documents()}


@app.post("/api/v1/documents", status_code=201)
def ingest_document(payload: IngestRequest):
    return service.ingest(payload.title, payload.category, payload.text)


@app.post("/api/v1/chat/ask")
def ask(payload: AskRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=422, detail="question must not be blank")
    return service.ask(payload.question, payload.top_k)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
