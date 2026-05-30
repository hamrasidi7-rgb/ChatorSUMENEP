from functools import lru_cache
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from rag.embeddings import get_embeddings
from config.settings import get_settings


def _ensure_index_exists(pc: Pinecone, index_name: str) -> None:
    existing = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing:
        # embed-multilingual-v3.0 menghasilkan dimensi 1024
        pc.create_index(
            name=index_name,
            dimension=1024,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )


@lru_cache
def get_vectorstore() -> PineconeVectorStore:
    settings = get_settings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    _ensure_index_exists(pc, settings.pinecone_index_name)

    return PineconeVectorStore(
        index=pc.Index(settings.pinecone_index_name),
        embedding=get_embeddings(),
        namespace=settings.pinecone_namespace,
    )
