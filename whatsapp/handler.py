"""
Handler untuk webhook OpenWA (@open-wa/wa-automate).

OpenWA mengirim POST ke /webhook setiap ada pesan masuk.
Setelah RAG menghasilkan jawaban, kita panggil OpenWA REST API
untuk mengirim balasan ke pengirim.
"""
import logging
import httpx
from typing import Any, Dict, Optional

from config.settings import get_settings

logger = logging.getLogger(__name__)


# ── Model payload dari OpenWA ────────────────────────────────────────────────

class IncomingMessage:
    """Representasi pesan masuk dari webhook OpenWA."""

    def __init__(self, payload: Dict[str, Any]):
        self.raw = payload
        # Teks pesan
        self.body: str = payload.get("body", "").strip()
        # ID chat pengirim, format: "6281234567890@c.us"
        self.chat_id: str = payload.get("from", "")
        # Tipe pesan (chat, image, document, dll.)
        self.msg_type: str = payload.get("type", "")
        # Apakah pesan dari diri sendiri (bot)
        self.from_me: bool = payload.get("fromMe", False)
        # Apakah pesan dari grup
        self.is_group: bool = "@g.us" in self.chat_id

    @property
    def is_text(self) -> bool:
        return self.msg_type == "chat"

    @property
    def should_respond(self) -> bool:
        """Hanya balas pesan teks yang bukan dari bot sendiri."""
        return self.is_text and not self.from_me and bool(self.body)


# ── OpenWA API Client ────────────────────────────────────────────────────────

async def send_message(chat_id: str, text: str) -> bool:
    """Kirim pesan balik ke pengguna via OpenWA REST API."""
    settings = get_settings()
    url = f"{settings.openwa_base_url.rstrip('/')}/sendText"

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if settings.openwa_api_key:
        headers["Authorization"] = f"Bearer {settings.openwa_api_key}"

    payload = {"chatId": chat_id, "content": text}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            logger.info(f"Pesan terkirim ke {chat_id}")
            return True
    except httpx.HTTPStatusError as e:
        logger.error(f"OpenWA HTTP error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        logger.error(f"Gagal mengirim pesan ke {chat_id}: {e}")
    return False


# ── Typing indicator ─────────────────────────────────────────────────────────

async def send_typing(chat_id: str) -> None:
    """Kirim indikator 'sedang mengetik...' ke pengguna."""
    settings = get_settings()
    url = f"{settings.openwa_base_url.rstrip('/')}/simulateTyping"

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if settings.openwa_api_key:
        headers["Authorization"] = f"Bearer {settings.openwa_api_key}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json={"chatId": chat_id, "typing": True}, headers=headers)
    except Exception:
        pass  # Typing indicator bersifat opsional, abaikan error


def parse_incoming(payload: Dict[str, Any]) -> Optional[IncomingMessage]:
    """Parsing payload webhook menjadi IncomingMessage, return None jika tidak valid."""
    try:
        msg = IncomingMessage(payload)
        return msg
    except Exception as e:
        logger.warning(f"Gagal parsing payload webhook: {e}")
        return None
