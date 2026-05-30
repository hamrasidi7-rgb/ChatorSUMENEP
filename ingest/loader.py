import logging
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredExcelLoader,
)

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".txt": TextLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
}


def load_document(file_path: Path) -> List[Document]:
    ext = file_path.suffix.lower()
    loader_cls = SUPPORTED_EXTENSIONS.get(ext)
    if loader_cls is None:
        logger.warning(f"Format tidak didukung, dilewati: {file_path.name}")
        return []

    try:
        loader = loader_cls(str(file_path))
        docs = loader.load()
        # Tambahkan metadata nama file
        for doc in docs:
            doc.metadata["source"] = file_path.name
            doc.metadata["file_path"] = str(file_path)
        logger.info(f"Loaded {len(docs)} halaman dari {file_path.name}")
        return docs
    except Exception as e:
        logger.error(f"Gagal memuat {file_path.name}: {e}")
        return []


def load_directory(directory: str | Path) -> List[Document]:
    directory = Path(directory)
    all_docs: List[Document] = []

    files = [f for f in directory.rglob("*") if f.is_file()]
    logger.info(f"Ditemukan {len(files)} file di {directory}")

    for file_path in files:
        docs = load_document(file_path)
        all_docs.extend(docs)

    logger.info(f"Total {len(all_docs)} halaman dokumen berhasil dimuat.")
    return all_docs
