from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM - Groq
    groq_api_key: str
    groq_model: str = "llama-3.1-70b-versatile"

    # Embedding - Cohere
    cohere_api_key: str
    cohere_embedding_model: str = "embed-multilingual-v3.0"

    # Vector DB - Pinecone
    pinecone_api_key: str
    pinecone_index_name: str = "chator-sumenep"
    pinecone_namespace: str = "pemkab-sumenep"

    # OpenWA
    openwa_base_url: str = "http://localhost:8002"
    openwa_api_key: str = ""

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    webhook_secret: str = ""

    # RAG
    retriever_top_k: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
