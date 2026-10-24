#!/usr/bin/env bash
# setup.sh — Instalador Master Unix/Linux/macOS do AIDD OUROBOROS
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "======================================================================"
echo " 🚀 [AIDD-OUROBOROS] Instalador Master & Sincronização Unix"
echo "======================================================================"

if ! command -v python3 &>/dev/null; then
    echo "[!] python3 não encontrado. Instale o Python 3.10+." >&2
    exit 1
fi

if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    echo "[*] Instalando dependências..."
    python3 -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
fi

python3 "$SCRIPT_DIR/ouroboros.py" --doctor
python3 "$SCRIPT_DIR/ouroboros.py" --audit

echo "======================================================================"
echo " 🌟 AIDD OUROBOROS OPERACIONAL COM SUCESSO!"
echo "======================================================================"
