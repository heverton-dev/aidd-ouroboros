#!/usr/bin/env bash
# sync_all.sh - Sincronizacao Global do Almoxarifado Central para Unix
# Autor: Heverton Eduardo Peres (2026)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Sincronizando skills do Almoxarifado Central ==="

for d in "$SCRIPT_DIR"/*/; do
    if [ -f "$d/SKILL.md" ] && [ -f "$d/sync.sh" ]; then
        echo "[*] Sincronizando $(basename "$d")..."
        bash "$d/sync.sh"
    fi
done

echo "[OK] Todas as skills foram sincronizadas com sucesso."
