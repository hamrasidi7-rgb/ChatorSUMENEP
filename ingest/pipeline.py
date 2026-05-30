import logging
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ingest.loader import load_directory
from rag.vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ".", " ", ""],
    length_function=len,
)


def split_documents(docs: List[Document]) -> List[Document]:
    chunks = TEXT_SPLITTER.split_documents(docs)
    logger.info(f"Dokumen dibagi menjadi {len(chunks)} chunk.")
    return chunks


def ingest(documents_dir: str | Path = "data/documents") -> int:
    """
    Muat semua dokumen dari direktori, bagi menjadi chunk,
    lalu upsert ke Pinecone vector store.
    Mengembalikan jumlah chunk yang berhasil diindeks.
    """
    documents_dir = Path(documents_dir)
    if not documents_dir.exists():
        raise FileNotFoundError(f"Direktori tidak ditemukan: {documents_dir}")

    logger.info("=== Memulai proses ingestion dokumen ===")

    # 1. Load
    docs = load_directory(documents_dir)
    if not docs:
        logger.warning("Tidak ada dokumen yang berhasil dimuat. Periksa isi folder data/documents/")
        return 0

    # 2. Split
    chunks = split_documents(docs)

    # 3. Embed + Upsert ke Pinecone
    logger.info("Mengunggah chunk ke Pinecone...")
    vectorstore = get_vectorstore()

    # Upsert batch per 100 agar tidak timeout
    batch_size = 100
    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        vectorstore.add_documents(batch)
        total += len(batch)
        logger.info(f"  Terupload: {total}/{len(chunks)} chunk")

    logger.info(f"=== Ingestion selesai: {total} chunk tersimpan di Pinecone ===")
    return total
