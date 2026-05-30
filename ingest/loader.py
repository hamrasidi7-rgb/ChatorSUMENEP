import logging
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)

logger = logging.getLogger(__name__)


def _load_excel(file_path: Path) -> List[Document]:
    """Load file Excel menggunakan pandas."""
    try:
        import pandas as pd
        dfs = pd.read_excel(str(file_path), sheet_name=None)
        docs = []
        for sheet_name, df in dfs.items():
            text = df.to_string(index=False)
            docs.append(Document(
                page_content=text,
                metadata={"source": file_path.name, "sheet": sheet_name},
            ))
        return docs
    except Exception as e:
        logger.error(f"Gagal memuat Excel {file_path.name}: {e}")
        return []


LOADERS = {
    ".pdf": lambda p: PyPDFLoader(str(p)).load(),
    ".docx": lambda p: Docx2txtLoader(str(p)).load(),
    ".txt": lambda p: TextLoader(str(p), encoding="utf-8").load(),
    ".xlsx": _load_excel,
    ".xls": _load_excel,
}


def load_document(file_path: Path) -> List[Document]:
    ext = file_path.suffix.lower()
    loader_fn = LOADERS.get(ext)
    if loader_fn is None:
        logger.warning(f"Format tidak didukung, dilewati: {file_path.name}")
        return []
    try:
        docs = loader_fn(file_path)
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
    files = [f for f in directory.rglob("*") if f.is_file() and f.suffix.lower() in LOADERS]
    logger.info(f"Ditemukan {len(files)} file dokumen di {directory}")
    for file_path in files:
        all_docs.extend(load_document(file_path))
    logger.info(f"Total {len(all_docs)} halaman dokumen berhasil dimuat.")
    return all_docs
