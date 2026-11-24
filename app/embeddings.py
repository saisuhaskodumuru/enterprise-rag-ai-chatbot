"""Embeddings.

Default: a deterministic TF-IDF embedding computed locally from the
corpus, labelled ``tfidf-local-v1``. It is not a neural embedding model;
it is the local fallback that keeps the demo runnable with no cloud
service and no API key.

When Azure OpenAI is configured (endpoint, API key, and an embedding
deployment), ``AzureEmbeddings`` uses LangChain's AzureOpenAIEmbeddings
instead. That path is real code, but it only runs when the environment
variables are set; it is never used in the default demo.
"""
import math
import re

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")

# Common words carry no topic signal. They are dropped from the TF-IDF
# vocabulary and from query matching so that short questions are matched
# on their content words (billing, refund, password) instead of on
# "how", "do", and "the".
STOPWORDS = frozenset(
    """
    a an the and or but if then else when at by for with about into through
    after over between out against during without before under around among
    of to in on is are was were be been being am do does did doing have has
    had having can could may might must shall should will would i you he she
    it we they me him her us them my your his its our their this that these
    those as from up down so than too very just how what which who whom why
    where when there here not no yes all any both each few more most other
    some such only own same s t don should now
    take takes took get gets got make makes made give gives gave go goes
    going come comes put puts set sets use uses used using need needs want
    wants know tells show shows find finds help helps
    """.split()
)


def _stem(token: str) -> str:
    # Light stemming so "refunds" matches "refund" and "takes" matches
    # "take". Only a trailing "s" is stripped, for tokens longer than 3.
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    return [
        _stem(token)
        for token in _TOKEN.findall(text.lower())
        if token not in STOPWORDS
    ]


class TfidfEmbeddings:
    """Deterministic TF-IDF vectors, L2-normalised for cosine search."""

    name = "tfidf-local-v1"

    def __init__(self) -> None:
        self.vocab: list[str] = []
        self.index: dict[str, int] = {}
        self.idf: np.ndarray = np.zeros(0)

    def fit(self, texts: list[str]) -> None:
        doc_freq: dict[str, int] = {}
        for text in texts:
            for token in set(tokenize(text)):
                doc_freq[token] = doc_freq.get(token, 0) + 1
        self.vocab = sorted(doc_freq)
        self.index = {token: i for i, token in enumerate(self.vocab)}
        n_docs = max(len(texts), 1)
        self.idf = np.array(
            [math.log((n_docs + 1) / (doc_freq[token] + 1)) + 1.0 for token in self.vocab],
            dtype=np.float64,
        )

    @property
    def dimension(self) -> int:
        return len(self.vocab)

    def embed(self, texts: list[str]) -> np.ndarray:
        if not self.vocab:
            raise ValueError("TF-IDF embeddings are not fitted yet")
        vectors = np.zeros((len(texts), len(self.vocab)), dtype=np.float64)
        for row, text in enumerate(texts):
            counts: dict[str, int] = {}
            for token in tokenize(text):
                counts[token] = counts.get(token, 0) + 1
            for token, count in counts.items():
                col = self.index.get(token)
                if col is not None:
                    vectors[row, col] = count * self.idf[col]
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return (vectors / norms).astype(np.float32)


class AzureEmbeddings:
    """Azure OpenAI embeddings via LangChain. Lazy import: only used
    when an embedding deployment is configured."""

    name = "azure-openai-embeddings"

    def __init__(self, endpoint: str, api_key: str, deployment: str, api_version: str):
        from langchain_openai import AzureOpenAIEmbeddings

        self._client = AzureOpenAIEmbeddings(
            azure_endpoint=endpoint,
            api_key=api_key,
            azure_deployment=deployment,
            api_version=api_version,
        )
        self._dimension: int | None = None

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            probe = np.array(self._client.embed_query("dimension probe"), dtype=np.float32)
            self._dimension = int(probe.shape[0])
        return self._dimension

    def embed(self, texts: list[str]) -> np.ndarray:
        vectors = np.array(self._client.embed_documents(list(texts)), dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return (vectors / norms).astype(np.float32)
