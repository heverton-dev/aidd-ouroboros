#!/usr/bin/env bash
# setup.sh — Instalador Master Unix/Linux/macOS do AIDD OUROBOROS (UV preferencial)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "======================================================================"
echo " 🚀 [AIDD-OUROBOROS] Instalador Master (UV preferencial)"
echo "======================================================================"

if ! command -v python3 &>/dev/null; then
    echo "[!] python3 não encontrado. Instale o Python 3.10+." >&2
    exit 1
fi

UV="$(command -v uv || true)"
installed=0

if [ -n "$UV" ]; then
    echo "[*] Instalando aidd-ouroboros via uv..."
    if [ ! -d "$SCRIPT_DIR/.venv" ]; then
        (cd "$SCRIPT_DIR" && "$UV" venv "$SCRIPT_DIR" --quiet) || true
    fi
    if [ -d "$SCRIPT_DIR/.venv" ]; then
        # shellcheck disable=SC1091
        source "$SCRIPT_DIR/.venv/bin/activate" 2>/dev/null || source "$SCRIPT_DIR/.venv/Scripts/activate" 2>/dev/null || true
        if (cd "$SCRIPT_DIR" && "$UV" pip install -e "$SCRIPT_DIR"); then
            installed=1
        else
            echo "[!] uv falhou; fallback para pip..."
        fi
    elif (cd "$SCRIPT_DIR" && "$UV" pip install --system -e "$SCRIPT_DIR"); then
        installed=1
    else
        echo "[!] uv falhou; fallback para pip..."
    fi
fi

if [ "$installed" -ne 1 ]; then
    echo "[*] Instalando aidd-ouroboros via pip (editável)..."
    python3 -m pip install -e "$SCRIPT_DIR"
fi

echo "[*] Sincronizando skills multi-harness (mestra primeiro)..."
if [ -f "$SCRIPT_DIR/aidd-skills/aidd-ouroboros-master/sync.sh" ]; then
    bash "$SCRIPT_DIR/aidd-skills/aidd-ouroboros-master/sync.sh" || true
fi
if [ -d "$SCRIPT_DIR/aidd-skills" ]; then
    for sync in "$SCRIPT_DIR"/aidd-skills/*/sync.sh; do
        [ -f "$sync" ] || continue
        name="$(basename "$(dirname "$sync")")"
        [ "$name" = "aidd-ouroboros-master" ] && continue
        echo "  -> $name"
        bash "$sync" || true
    done
fi

export AIDD_OUROBOROS_ROOT="$SCRIPT_DIR"

echo "[*] Doctor..."
python3 "$SCRIPT_DIR/ouroboros.py" --doctor
echo "[*] Master doctor..."
python3 "$SCRIPT_DIR/ouroboros.py" --master-doctor
echo "[*] Quality Gates..."
python3 "$SCRIPT_DIR/ouroboros.py" --audit

echo "======================================================================"
echo " 🌟 AIDD OUROBOROS OPERACIONAL COM SUCESSO"
echo "======================================================================"
echo " Uso:"
echo "   ouroboros --from-nl \"criar pipeline X a partir de https://y\""
echo "   ouroboros --orchestrate ./SPEC_PIPELINE.json"
echo "   /ouroboros   (no harness de agentes)"
