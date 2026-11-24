"""Configuration, read only from environment variables.

No credentials are hard-coded. The Azure OpenAI integration is active
only when AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are both set.
"""
import os


class Settings:
    azure_openai_endpoint: str | None = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = os.environ.get("AZURE_OPENAI_API_KEY")
    # Name of the GPT-4 deployment in the Azure OpenAI resource.
    azure_openai_deployment: str = os.environ.get(
        "AZURE_OPENAI_DEPLOYMENT", "gpt-4"
    )
    azure_openai_api_version: str = os.environ.get(
        "AZURE_OPENAI_API_VERSION", "2024-02-01"
    )
    # Name of the Azure OpenAI embedding deployment, if one is configured.
    azure_openai_embedding_deployment: str | None = os.environ.get(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
    )
    chunk_size: int = int(os.environ.get("RAG_CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.environ.get("RAG_CHUNK_OVERLAP", "50"))
    default_top_k: int = int(os.environ.get("RAG_TOP_K", "3"))

    @property
    def azure_configured(self) -> bool:
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)


settings = Settings()
