from functools import lru_cache
from langchain_cohere import CohereEmbeddings
from config.settings import get_settings


@lru_cache
def get_embeddings() -> CohereEmbeddings:
    settings = get_settings()
    return CohereEmbeddings(
        cohere_api_key=settings.cohere_api_key,
        model=settings.cohere_embedding_model,
    )
