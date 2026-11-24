# Enterprise RAG AI Chatbot

A real working demo of a document-aware customer-support chatbot. Ask a
question in plain English and it retrieves the relevant support
documents and answers from them, with the sources cited.
It is a demo rebuild of the RAG chatbot work Sai Suhas Kodumuru did at
Verizon. It is not Verizon production code, and it contains no real
customer data. Every document in it is synthetic.

## What it does

- Answers a question from the seeded support documents, with the
  retrieved chunks shown as sources with their similarity scores.
- Says which model produced the answer: `azure-openai-gpt-4` when Azure
  OpenAI is configured, otherwise `local-extractive-v1`.
- Lists the support documents and lets you ingest a new one through the
  API; the new document is chunked, embedded, and retrievable
  immediately.
- Says plainly when it cannot find an answer in the documents, instead
  of inventing one.
- Serves a chat UI at the root URL that calls the real API.

## Architecture

```
Browser / curl
      |
      v
Static chat UI (static/index.html)
      |
      v
FastAPI, Python 3.12  (app/main.py, /api/v1/...)
      |
      +--> RagService (app/rag.py)
      |       |
      |       +--> RecursiveCharacterTextSplitter (LangChain)
      |       |     chunks documents, 500 chars with 50 overlap
      |       |
      |       +--> Embeddings (app/embeddings.py)
      |       |     TF-IDF, local, deterministic (tfidf-local-v1)
      |       |     -- or AzureOpenAIEmbeddings when configured
      |       |
      |       +--> FaissVectorStore (app/vector_store.py)
      |             FAISS IndexFlatIP, cosine search, with an
      |             IDF-weighted rerank of the top candidates
      |
      +--> Generation
              |
              +--> AzureChatOpenAI, GPT-4 (only when
              |     AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY
              |     are set; on any failure it falls back)
              |
              +--> Local extractive generator (local-extractive-v1):
                    the best-matching sentences from the top chunk
```

No database. No persistence. All documents live only for the life of
the process, so a document ingested through the API disappears on
restart. The seeded documents are loaded on every startup.

## Retrieval, in detail

The local embedding is TF-IDF over the chunked corpus, L2-normalised,
so FAISS cosine search works on it. Two things keep short questions
accurate:

- A stopword list (articles, pronouns, and generic verbs such as
  "take", "get", and "make") is dropped from matching, so a question
  is matched on its content words. Without this, "How long do refunds
  take?" retrieved the plan document, which mentions "take" twice and
  "refund" once, instead of the refunds document.
- After FAISS returns its top candidates, they are reranked by the
  IDF-weighted overlap of content words with the question, so a rare
  content word ("refund") counts for more than a common one.
- Tokens are lightly stemmed (a trailing "s" is stripped), so
  "refunds" matches "refund" and "takes" matches "take".

## How to run

Requirements: Python 3.12.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python run.py
```

Then open http://localhost:8000 in a browser.

## API examples

Ask a question (billing — the top source should be the billing
document):

```bash
curl -s -X POST http://localhost:8000/api/v1/chat/ask \
  -H 'Content-Type: application/json' \
  -d '{"question": "How do I change my payment method?"}'
```

List documents:

```bash
curl -s http://localhost:8000/api/v1/documents
```

Ingest a document (it is retrievable immediately):

```bash
curl -s -X POST http://localhost:8000/api/v1/documents \
  -H 'Content-Type: application/json' \
  -d '{"title": "Store opening hours", "category": "stores",
       "text": "The downtown store opens at nine in the morning and
       closes at nine in the evening on weekdays."}'
```

Stats:

```bash
curl -s http://localhost:8000/api/v1/stats
```

## How Azure OpenAI would plug in

The service tries Azure OpenAI GPT-4 first, and only when it is
configured. Set these environment variables:

```bash
export AZURE_OPENAI_ENDPOINT="https://<resource>.openai.azure.com/"
export AZURE_OPENAI_API_KEY="<key>"
export AZURE_OPENAI_DEPLOYMENT="gpt-4"
export AZURE_OPENAI_API_VERSION="2024-02-01"
# Optional: use Azure embeddings instead of local TF-IDF
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="<embedding-deployment>"
.venv/bin/python run.py
```

The generator (`RagService._generate_with_azure`) sends the retrieved
chunks and the question to the GPT-4 deployment through LangChain's
`AzureChatOpenAI`, with a prompt that says to answer only from the
documents. When the call succeeds the response says
`"model": "azure-openai-gpt-4"`. When no endpoint is configured, or the
call fails for any reason, the service falls back to the local
extractive generator and the response says
`"model": "local-extractive-v1"`. The API key is sent only as a header
to the configured endpoint and is never logged.

In the Verizon work this pattern was the same: LangChain RAG
pipelines retrieved from a FAISS index and Azure OpenAI GPT-4
generated the answer, with the retrieved chunks kept as citations.
This demo keeps that shape, with a local TF-IDF embedding and an
extractive generator standing in for the cloud services when no
endpoint is present.

## Tests

```bash
.venv/bin/python -m pytest tests/ -v
```

Tests cover retrieval (a billing question retrieves the billing
document, a refund question retrieves the returns document), the ask
endpoint (a password question returns 200 with an answer from the
account document and at least one source), ingestion (a newly ingested
document is retrievable), and validation (a two-character question is
rejected with 422).

## Data

All data is synthetic. Eight seeded support documents cover billing,
account and password recovery, orders and shipping, returns and
refunds, router setup and connection problems, warranty and repairs,
plan changes and cancellation, and account security. They chunk into
19 chunks. No real customer, account, or order data is used.
