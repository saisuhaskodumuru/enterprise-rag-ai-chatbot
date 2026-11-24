# Case Study: Enterprise RAG AI Chatbot

## What this is

This is a demo rebuild of RAG chatbot work I did at Verizon, built as
a standalone portfolio project. It is not Verizon production code, and
it contains no real customer data. Every document in it is synthetic.
The goal was to show the same shape of system in a form anyone can run
locally: a FastAPI service that chunks support documents with
LangChain, retrieves the relevant chunks from a FAISS vector store,
and answers with Azure OpenAI GPT-4 when it is configured — or with a
local extractive generator when it is not — while always citing the
sources it used.

## Problem

Support teams answer the same questions again and again, and the
answers live in documents that agents have to search by hand. A
chatbot that answers from its own training alone will invent details —
a wrong refund window, a wrong fee — and a customer will act on them.
A RAG chatbot fixes that by grounding every answer in retrieved
documents, but only if the retrieval is good: a wrong document means a
confident wrong answer, and a system that only works when the cloud
model is up does not survive an outage. The Verizon work had the same
constraints at production scale: a large support knowledge base, a
FAISS index, and GPT-4 answers that had to stay grounded in the
retrieved chunks.

## My role

At Verizon I worked on the LangChain RAG pipelines and Azure OpenAI
GPT-4 integration for customer support, with FAISS retrieval over the
support documents. In this demo I rebuilt the pattern end to end: the
document set, the LangChain chunking, the embedding and FAISS vector
store, the reranking, the Azure OpenAI integration point, the local
extractive fallback, the REST API, the chat UI, and the tests.

## Architecture

```
Browser chat UI (static HTML/CSS/JS)
        |
        |  REST / JSON
        v
FastAPI app  --  POST /api/v1/chat/ask
                 GET  /api/v1/documents
                 POST /api/v1/documents
                 GET  /api/v1/stats
                 GET  /api/v1/health
        |
        v
RagService
        |
        +--> RecursiveCharacterTextSplitter (LangChain)
        |     500 chars, 50 overlap
        |            |
        |            v
        +--> Embeddings
        |     TF-IDF, local, deterministic (tfidf-local-v1)
        |     -- or AzureOpenAIEmbeddings when configured
        |            |
        |            v
        +--> FAISS IndexFlatIP (cosine search)
        |     + IDF-weighted rerank of the top candidates
        |            |
        |            v
        +--> Generation
              |                          |
              | Azure OpenAI configured? | no, or Azure fails
              v                          v
        AzureChatOpenAI (GPT-4)    Local extractive generator
        (LangChain)                (local-extractive-v1)
```

Retrieval is FAISS cosine search over TF-IDF vectors, followed by a
rerank that weights matched content words by IDF, so a rare content
word counts for more than a common one. Generation tries Azure OpenAI
GPT-4 first when configured and falls back to the local extractive
generator, which returns the best-matching sentences from the top
retrieved chunk. The response always says which model produced the
answer and always lists the retrieved chunks as sources with their
scores. If the best chunk scores below 0.05, the chatbot says it could
not find an answer instead of inventing one.

## What was built

- A Python 3.12, FastAPI service with no database. All state is in
  memory, which keeps the demo self-contained; ingested documents
  disappear on restart.
- Five endpoints: ask a question, list documents, ingest a document,
  stats, and health.
- Eight synthetic seeded support documents (billing, account and
  password recovery, orders and shipping, returns and refunds, router
  setup, warranty and repairs, plan changes, account security) that
  chunk into 19 chunks on startup.
- A real LangChain chunking step (`RecursiveCharacterTextSplitter`),
  a real FAISS vector store (`IndexFlatIP`), and real LangChain Azure
  OpenAI clients (`AzureChatOpenAI`, `AzureOpenAIEmbeddings`) that
  activate only when the environment variables are set.
- A local TF-IDF embedding with a stopword list, light stemming, and
  an IDF-weighted rerank, all labelled honestly as local
  (`tfidf-local-v1`, `local-extractive-v1`) so nobody mistakes the
  fallback for a neural model.
- A static chat UI with no build step and no external JavaScript: a
  question box, example questions, answers with the model that
  produced them, and expandable sources with scores. It calls the real
  API.
- Tests: 2 retrieval tests, 2 ask-endpoint tests (a correct answer
  with sources, and a 422 validation failure), 1 ingestion test, and
  1 stats/documents test.

## Results, measured on this demo

These numbers were measured locally on 2026-11-24 by running the
application and curling the real endpoints. They describe the demo
only. No Azure OpenAI endpoint was configured, so every answer below
came from the local extractive generator.

- Tests: 6 run, 0 failures, 0 errors, in 0.99 s (final run on the
  finished code).
- Application startup: 0.86 s from launch to the first healthy
  response from `/api/v1/health`.
- Seeded index at startup: 8 documents, 19 chunks, embedding model
  `tfidf-local-v1`, vector store FAISS, generation model
  `local-extractive-v1`.
- `POST /api/v1/chat/ask`, "How do I change my payment method?":
  HTTP 200, answer latency 0.7 ms, top source DOC-BILLING-001
  (score 0.4084). The answer gives the Billing, then Payment Methods
  steps.
- `POST /api/v1/chat/ask`, "How long do refunds take?": HTTP 200,
  answer latency 0.8 ms, top source DOC-RETURNS-001 (score 0.1960).
  The answer gives the five-to-seven business day refund window.
- `POST /api/v1/chat/ask`, "How do I reset my password?": HTTP 200,
  answer latency 0.7 ms, top source DOC-ACCOUNT-001 (score 0.4057).
  The answer gives the Forgot Password link and the 15-minute reset
  code.
- `POST /api/v1/chat/ask`, "How long does standard shipping take?":
  HTTP 200, answer latency 0.7 ms, top source DOC-ORDERS-001
  (score 0.2910), 2 sources. The answer gives the three-to-five
  business day standard shipping time.
- `POST /api/v1/chat/ask`, "What does the warranty cover?": HTTP 200,
  answer latency 0.6 ms, top source DOC-WARRANTY-001 (score 0.3658).
  The answer gives the one-year limited warranty for manufacturing
  defects.
- `POST /api/v1/documents`, a store-opening-hours document: HTTP 201
  in 0.0061 s, 1 chunk, totals 9 documents and 20 chunks. Asking
  "What time does the downtown store open?" afterwards returned
  HTTP 200 in 0.0030 s, answer latency 0.8 ms, top source the new
  document (score 0.2977), with the correct opening hours.
- `POST /api/v1/chat/ask` with a two-character question: HTTP 422,
  "String should have at least 3 characters".
- `POST /api/v1/chat/ask`, "What is the capital of France?": HTTP 200
  in 0.0032 s, answer latency 0.7 ms, with the answer "I couldn't
  find an answer to that in the support documents I have" and 0
  sources — the chatbot refused to answer from outside its documents.
- Chat UI at `http://localhost:8000/`: HTTP 200 in 0.030 s, 5,909
  bytes of static HTML, CSS, and JavaScript.

No production metrics are claimed here. Any latency or scale results
from the Verizon work are production results from that project and are
not claims about this demo.

## Challenges

- The first retrieval pass was wrong in a way that mattered: "How
  long do refunds take?" returned the plan document, because that
  document mentions "take" twice and "refund" once, while the refunds
  document matches only "refund". I fixed it in two steps. First, a
  stopword list that drops generic verbs such as "take", "get", and
  "make" from matching, so questions are matched on content words.
  Second, an IDF-weighted rerank of the FAISS candidates, so a rare
  content word ("refund") counts for more than a common one. After
  both changes the refund question retrieves the returns document
  with the five-to-seven business day answer, and the other headline
  questions still retrieve their correct documents.
- Smaller chunks made retrieval worse, not better: at 300 characters
  the password question retrieved the router factory-reset chunk
  instead of the account document. I kept the 500-character chunks
  and fixed retrieval with the stopwords and rerank instead.
- The LangChain text splitter drops the ". " separator at chunk
  boundaries, so some chunks arrived with a leading ". " and some
  sentences arrived without a final period. The chunk text is cleaned
  when chunks are built, and the local generator restores a missing
  final period on the sentences it returns.
- The local extractive generator first pulled sentences from every
  retrieved chunk, which mixed unrelated advice into answers — a
  security sentence in an answer about payment methods. It now
  answers only from the top-ranked chunk, which keeps the answer
  on-topic at the cost of shorter answers. The Azure GPT-4 path,
  when configured, synthesises across all retrieved chunks instead.

## Tech stack

Python 3.12, FastAPI, Uvicorn, LangChain (chunking and Azure OpenAI
clients), FAISS (faiss-cpu, IndexFlatIP), NumPy, Pydantic, pytest,
vanilla HTML/CSS/JS chat UI. Local fallback: TF-IDF embeddings and an
extractive generator, both labelled as local. No database.
