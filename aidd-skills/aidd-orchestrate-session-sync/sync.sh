#!/usr/bin/env bash
# Instala a skill aidd-orchestrate-session-sync nos harnesses
NAME="aidd-orchestrate-session-sync"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
H="$HOME"

DIRS=(
  "$H/.agents/skills"
  "$H/.claude/skills"
  "$H/.config/opencode/skills"
  "$H/.gemini/skills"
  "$H/.cursor/skills"
)

for d in "${DIRS[@]}"; do
  if [ -d "$d" ]; then
    mkdir -p "$d/$NAME"
    cp -r "$SRC"/* "$d/$NAME/"
    echo "OK   $d/$NAME"
  fi
done
