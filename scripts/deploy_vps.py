"""
Script deploy otomatis ChatorSUMENEP ke VPS via SSH.
Jalankan sekali dari lokal untuk setup lengkap di VPS.
"""
import sys
import time
import paramiko

import os
from pathlib import Path
from dotenv import load_dotenv

# Baca konfigurasi dari .env lokal
load_dotenv(Path(__file__).parent.parent / ".env")

VPS_HOST = os.getenv("VPS_HOST", "187.77.119.148")
VPS_USER = os.getenv("VPS_USER", "root")
VPS_PASS = os.getenv("VPS_PASS", "")  # Set via env var VPS_PASS=... python scripts/deploy_vps.py

REPO_URL = "https://github.com/hamrasidi7-rgb/ChatorSUMENEP.git"
APP_DIR  = "/opt/chator-sumenep"

# Baca .env lokal dan kirim ke VPS
def _read_local_env() -> str:
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        return env_path.read_text(encoding="utf-8")
    return "# Isi API key di sini\n"

ENV_CONTENT = _read_local_env()

SYSTEMD_SERVICE = """[Unit]
Description=ChatorSUMENEP RAG Chatbot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={app_dir}
EnvironmentFile={app_dir}/.env
ExecStart={app_dir}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
""".format(app_dir=APP_DIR)


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 120) -> str:
    print(f"\n>>> {cmd[:80]}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    if out.strip():
        print(out.strip())
    if err.strip():
        # Filter benign warnings
        for line in err.strip().splitlines():
            if any(w in line for w in ["WARNING", "WARN", "warning", "dpkg-preconfigure"]):
                continue
            print(f"[STDERR] {line}")
    return out


def write_file(sftp: paramiko.SFTPClient, remote_path: str, content: str) -> None:
    with sftp.open(remote_path, "w") as f:
        f.write(content)
    print(f"    Tulis: {remote_path}")


def main():
    print("=" * 60)
    print("  ChatorSUMENEP — Deploy ke VPS")
    print(f"  Host : {VPS_HOST}")
    print("=" * 60)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print("\n[1/8] Menghubungkan ke VPS...")
    client.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=30)
    print("      Terhubung!")

    sftp = client.open_sftp()

    print("\n[2/8] Update sistem & install dependensi sistem...")
    run(client, "apt-get update -qq", timeout=120)
    run(client, "apt-get install -y -qq python3 python3-pip python3-venv git curl 2>&1 | tail -5", timeout=180)

    print("\n[3/8] Clone / update repository...")
    run(client, f"if [ -d {APP_DIR}/.git ]; then cd {APP_DIR} && git pull; else git clone {REPO_URL} {APP_DIR}; fi", timeout=60)

    print("\n[4/8] Buat virtual environment & install requirements...")
    run(client, f"cd {APP_DIR} && python3 -m venv venv", timeout=60)
    run(client, f"cd {APP_DIR} && venv/bin/pip install -q --upgrade pip", timeout=60)
    run(client, f"cd {APP_DIR} && venv/bin/pip install -q -r requirements.txt 2>&1 | tail -10", timeout=600)

    print("\n[5/8] Tulis file .env...")
    write_file(sftp, f"{APP_DIR}/.env", ENV_CONTENT)

    print("\n[6/8] Cek port OpenWA yang berjalan...")
    out = run(client, "ss -tlnp | grep -E '3000|3001|8002|8080' 2>/dev/null || echo 'Cek manual'")
    if not out.strip() or "Cek manual" in out:
        out2 = run(client, "pm2 list 2>/dev/null || echo 'pm2 tidak ditemukan'")
        print(f"Status pm2: {out2.strip()}")

    print("\n[7/8] Setup systemd service...")
    write_file(sftp, "/etc/systemd/system/chator-sumenep.service", SYSTEMD_SERVICE)
    run(client, "systemctl daemon-reload")
    run(client, "systemctl enable chator-sumenep")
    run(client, "systemctl restart chator-sumenep")
    time.sleep(3)

    print("\n[8/8] Verifikasi status service...")
    run(client, "systemctl status chator-sumenep --no-pager -l | head -20")
    run(client, "curl -s http://localhost:8000/ || echo 'Server belum merespons'")

    sftp.close()
    client.close()

    print("\n" + "=" * 60)
    print("  DEPLOY SELESAI!")
    print(f"  URL server    : http://{VPS_HOST}:8000")
    print(f"  Webhook URL   : http://{VPS_HOST}:8000/webhook")
    print(f"  Health check  : http://{VPS_HOST}:8000/health")
    print("=" * 60)


if __name__ == "__main__":
    main()
