"""
ChatorSUMENEP — Chatbot RAG Pemerintah Kabupaten Sumenep
Entry point FastAPI: menerima webhook dari OpenWA, menjawab via RAG, membalas via OpenWA API.
"""
import logging
import hashlib
import hmac
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse

from config.settings import get_settings
from rag.chain import ask, get_chain
from whatsapp.handler import parse_incoming, send_message, send_typing

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Startup ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inisialisasi RAG chain...")
    get_chain()   # Build chain sekali saat startup
    logger.info("ChatorSUMENEP siap menerima pesan!")
    yield
    logger.info("Server berhenti.")


app = FastAPI(
    title="ChatorSUMENEP",
    description="Chatbot RAG Pemerintah Kabupaten Sumenep",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Security ─────────────────────────────────────────────────────────────────

def verify_webhook_signature(request_body: bytes, signature: str) -> bool:
    """Verifikasi HMAC-SHA256 signature dari OpenWA (jika dikonfigurasi)."""
    settings = get_settings()
    if not settings.webhook_secret:
        return True  # Jika tidak ada secret, lewati verifikasi
    expected = hmac.new(
        settings.webhook_secret.encode(),
        request_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


# ── Background task ───────────────────────────────────────────────────────────

async def process_message(chat_id: str, question: str) -> None:
    """Proses pertanyaan dengan RAG dan kirim jawaban ke WhatsApp."""
    try:
        await send_typing(chat_id)
        logger.info(f"[{chat_id}] Pertanyaan: {question!r}")
        answer = await ask(question)
        logger.info(f"[{chat_id}] Jawaban: {answer[:80]}...")
        await send_message(chat_id, answer)
    except Exception as e:
        logger.error(f"[{chat_id}] Error saat memproses pesan: {e}")
        await send_message(
            chat_id,
            "Mohon maaf, terjadi kendala teknis. Silakan coba lagi atau hubungi "
            "Dinas Komunikasi dan Informatika Kab. Sumenep.",
        )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "ChatorSUMENEP"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.post("/webhook", tags=["WhatsApp"])
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint yang dipanggil oleh OpenWA setiap kali ada pesan masuk.
    Payload diproses secara asinkron agar webhook segera merespons 200.
    """
    body = await request.body()

    # Opsional: verifikasi signature
    signature = request.headers.get("x-hub-signature-256", "")
    if not verify_webhook_signature(body, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    try:
        payload: Dict[str, Any] = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    msg = parse_incoming(payload)

    if msg is None or not msg.should_respond:
        return JSONResponse({"status": "ignored"})

    # Jalankan RAG di background agar webhook langsung return 200
    background_tasks.add_task(process_message, msg.chat_id, msg.body)

    return JSONResponse({"status": "processing"})


# ── Entrypoint ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )
