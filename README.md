# ChatorSUMENEP 🤖

**Chatbot RAG Pemerintah Kabupaten Sumenep**

Chatbot berbasis *Retrieval-Augmented Generation* (RAG) yang menjawab pertanyaan masyarakat seputar pelayanan publik, program, kebijakan, dan capaian kinerja Pemerintah Kabupaten Sumenep melalui WhatsApp.

---

## Arsitektur

```
WhatsApp (User)
      │
      ▼
  OpenWA (VPS) ──── POST /webhook ────▶ ChatorSUMENEP (FastAPI)
                                               │
                        ┌──────────────────────┤
                        │                      │
                        ▼                      ▼
                  Pinecone (Retrieve)     Groq LLM (Generate)
                  [Cohere Embeddings]
                        │                      │
                        └──────────┬───────────┘
                                   ▼
                              Jawaban RAG
                                   │
                        ◀── send /sendText ──────
```

| Komponen         | Teknologi                             |
|-----------------|---------------------------------------|
| LLM             | Groq (`llama-3.1-70b-versatile`)      |
| Embedding       | Cohere (`embed-multilingual-v3.0`)    |
| Vector Database | Pinecone (Serverless)                 |
| RAG Framework   | LangChain                             |
| WhatsApp        | OpenWA (@open-wa/wa-automate)         |
| API Server      | FastAPI + Uvicorn                     |

---

## Cara Setup

### 1. Clone & Install

```bash
git clone https://github.com/hamrasidi7-rgb/ChatorSUMENEP.git
cd ChatorSUMENEP
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Konfigurasi Environment

```bash
cp .env.example .env
# Edit .env dan isi semua API key
```

| Variabel               | Keterangan                                      |
|------------------------|-------------------------------------------------|
| `GROQ_API_KEY`         | API key dari console.groq.com                   |
| `COHERE_API_KEY`       | API key dari dashboard.cohere.com               |
| `PINECONE_API_KEY`     | API key dari app.pinecone.io                    |
| `PINECONE_INDEX_NAME`  | Nama index Pinecone (buat manual atau otomatis) |
| `OPENWA_BASE_URL`      | URL VPS tempat OpenWA berjalan                  |
| `OPENWA_API_KEY`       | API key OpenWA (jika dikonfigurasi)             |
| `WEBHOOK_SECRET`       | Secret untuk verifikasi webhook (opsional)      |

### 3. Tambahkan Dokumen OPD

Taruh file PDF, DOCX, TXT, atau XLSX di folder `data/documents/`:

```
data/documents/
├── RPJMD_Sumenep_2021-2026.pdf
├── Renstra_Diskominfo_2021-2026.pdf
├── LKjIP_2023.pdf
└── ...
```

### 4. Ingest Dokumen ke Pinecone

```bash
python scripts/ingest_docs.py
```

### 5. Konfigurasi OpenWA

Di VPS tempat OpenWA berjalan, set webhook URL ke:

```
http://<IP-SERVER-CHATOR>:8000/webhook
```

### 6. Jalankan Server

```bash
python main.py
# atau
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Struktur Proyek

```
ChatorSUMENEP/
├── main.py                  # FastAPI app & webhook endpoint
├── config/
│   └── settings.py          # Konfigurasi via .env
├── rag/
│   ├── embeddings.py        # Cohere embeddings
│   ├── vectorstore.py       # Pinecone vector store
│   └── chain.py             # LangChain RAG chain
├── ingest/
│   ├── loader.py            # Document loader (PDF/DOCX/TXT/XLSX)
│   └── pipeline.py          # Ingestion pipeline
├── whatsapp/
│   └── handler.py           # OpenWA webhook & API client
├── scripts/
│   └── ingest_docs.py       # CLI untuk ingest dokumen
├── data/
│   └── documents/           # Taruh dokumen OPD di sini
├── requirements.txt
└── .env.example
```

---

## API Endpoints

| Method | Path       | Deskripsi                              |
|--------|-----------|----------------------------------------|
| GET    | `/`        | Health check                           |
| GET    | `/health`  | Health check detail                    |
| POST   | `/webhook` | Menerima pesan masuk dari OpenWA       |

---

## Deployment di VPS

```bash
# Install dengan systemd
sudo nano /etc/systemd/system/chator-sumenep.service
```

```ini
[Unit]
Description=ChatorSUMENEP RAG Chatbot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/ChatorSUMENEP
ExecStart=/home/ubuntu/ChatorSUMENEP/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable chator-sumenep
sudo systemctl start chator-sumenep
```
