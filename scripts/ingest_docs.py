"""
Script untuk mengingest dokumen OPD ke Pinecone.

Cara pakai:
    python scripts/ingest_docs.py
    python scripts/ingest_docs.py --dir path/ke/folder/dokumen
"""
import sys
import argparse
import logging
from pathlib import Path

# Agar import dari root project bisa berjalan
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from ingest.pipeline import ingest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)


def main():
    parser = argparse.ArgumentParser(
        description="Ingest dokumen OPD Pemkab Sumenep ke Pinecone vector database."
    )
    parser.add_argument(
        "--dir",
        default="data/documents",
        help="Direktori yang berisi dokumen (default: data/documents)",
    )
    args = parser.parse_args()

    total = ingest(args.dir)
    if total:
        print(f"\n[OK] Berhasil mengindeks {total} chunk ke Pinecone.")
    else:
        print("\n[!] Tidak ada chunk yang diindeks. Periksa isi folder dokumen.")


if __name__ == "__main__":
    main()
