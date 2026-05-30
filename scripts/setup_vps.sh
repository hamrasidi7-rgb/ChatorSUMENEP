#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# ChatorSUMENEP — Setup lengkap di VPS
# Jalankan di terminal VPS (copy-paste semuanya sekaligus):
#   bash <(curl -fsSL https://raw.githubusercontent.com/hamrasidi7-rgb/ChatorSUMENEP/main/scripts/setup_vps.sh)
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_DIR="/opt/chator-sumenep"
REPO="https://github.com/hamrasidi7-rgb/ChatorSUMENEP.git"

echo ""
echo "============================================================"
echo "  ChatorSUMENEP — Setup VPS Pemkab Sumenep"
echo "============================================================"

# ── 1. Sistem ────────────────────────────────────────────────────────────────
echo "[1/7] Update sistem & install Python3, git..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git curl ufw

# ── 2. Clone repo ────────────────────────────────────────────────────────────
echo "[2/7] Clone repository..."
if [ -d "$APP_DIR/.git" ]; then
  echo "  Repo sudah ada, pull update..."
  cd "$APP_DIR" && git pull
else
  git clone "$REPO" "$APP_DIR"
fi

# ── 3. Virtual environment ───────────────────────────────────────────────────
echo "[3/7] Buat virtual environment & install requirements..."
cd "$APP_DIR"
python3 -m venv venv
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

# ── 4. File .env ─────────────────────────────────────────────────────────────
echo "[4/7] Tulis file .env..."
cat > "$APP_DIR/.env" << 'ENVEOF'
GROQ_API_KEY=ISI_GROQ_API_KEY_ANDA
GROQ_MODEL=llama-3.1-70b-versatile

COHERE_API_KEY=ISI_COHERE_API_KEY_ANDA
COHERE_EMBEDDING_MODEL=embed-multilingual-v3.0

PINECONE_API_KEY=ISI_PINECONE_API_KEY_ANDA
PINECONE_INDEX_NAME=chator-sumenep
PINECONE_NAMESPACE=pemkab-sumenep

OPENWA_BASE_URL=http://localhost:3000
OPENWA_API_KEY=

APP_HOST=0.0.0.0
APP_PORT=8000
WEBHOOK_SECRET=

RETRIEVER_TOP_K=5
ENVEOF

chmod 600 "$APP_DIR/.env"

# ── 5. Cek OpenWA ────────────────────────────────────────────────────────────
echo "[5/7] Deteksi port OpenWA..."
OPENWA_PORT=""
for PORT in 3000 3001 8002 8080; do
  if ss -tlnp | grep -q ":$PORT "; then
    OPENWA_PORT=$PORT
    echo "  OpenWA terdeteksi di port $PORT"
    # Update .env dengan port yang benar
    sed -i "s|OPENWA_BASE_URL=.*|OPENWA_BASE_URL=http://localhost:$PORT|" "$APP_DIR/.env"
    break
  fi
done
if [ -z "$OPENWA_PORT" ]; then
  echo "  [!] OpenWA tidak terdeteksi. Pastikan OpenWA berjalan dulu."
  echo "  [!] Edit /opt/chator-sumenep/.env dan set OPENWA_BASE_URL yang benar."
fi

# ── 6. Firewall ──────────────────────────────────────────────────────────────
echo "[6/7] Buka port 8000 di firewall..."
ufw allow 8000/tcp 2>/dev/null || true

# ── 7. Systemd service ───────────────────────────────────────────────────────
echo "[7/7] Setup dan start systemd service..."
cat > /etc/systemd/system/chator-sumenep.service << SVCEOF
[Unit]
Description=ChatorSUMENEP RAG Chatbot Pemkab Sumenep
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$APP_DIR/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable chator-sumenep
systemctl restart chator-sumenep

sleep 3
echo ""
echo "============================================================"
echo "  Verifikasi server..."
curl -s http://localhost:8000/ && echo ""
echo ""
echo "  SETUP SELESAI!"
echo ""
echo "  URL Webhook OpenWA : http://187.77.119.148:8000/webhook"
echo "  Health check       : http://187.77.119.148:8000/health"
echo ""
echo "  Perintah berguna:"
echo "    systemctl status chator-sumenep   # cek status"
echo "    journalctl -u chator-sumenep -f   # lihat log"
echo "============================================================"
