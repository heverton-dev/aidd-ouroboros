#!/usr/bin/env sh
# Instala a skill aidd-materialize-tutorial-stitch em NIVEL GLOBAL nas harnesses da maquina.
# Fonte: a pasta deste script. Uso: sh sync.sh [--dry-run]
set -eu
name=aidd-materialize-tutorial-stitch
src=$(cd "$(dirname "$0")" && pwd)
dry=0
[ "${1:-}" = "--dry-run" ] && dry=1
for t in "$HOME/.agents/skills" "$HOME/.claude/skills" "$HOME/.config/opencode/skills" "$HOME/.opencode/skills" \
         "$HOME/.gemini/skills" "$HOME/.gemini/antigravity/skills" "$HOME/.gemini/antigravity-cli/skills" \
         "$HOME/.gemini/antigravity-ide/skills" "$HOME/.hermes/skills" "$HOME/.cline/skills" \
         "$HOME/.factory/skills" "$HOME/.mimocode/skills"; do
  case "$t" in
    "$HOME/.agents/skills") ;;
    *) [ -d "$t" ] || { echo "SKIP  $t (harness ausente)"; continue; } ;;
  esac
  dest="$t/$name"
  if [ -d "$dest" ] && [ "$(cd "$dest" && pwd)" = "$src" ]; then echo "SKIP  $dest (mesma fonte)"; continue; fi
  if [ $dry -eq 1 ]; then echo "DRY   $dest"; continue; fi
  mkdir -p "$dest"
  cp -R "$src/." "$dest/"
  rm -rf "$dest/scripts/__pycache__" "$dest/graphify-out" "$dest/.graphifyignore"
  echo "OK    $dest"
done
for pair in "$HOME/.claude/commands:$name.md" "$HOME/.gemini/antigravity/commands:$name.md" "$HOME/.gemini/commands:$name.toml"; do
  dir=${pair%%:*}; file=${pair#*:}
  [ -d "$dir" ] || { echo "SKIP  $dir (ausente)"; continue; }
  if [ $dry -eq 1 ]; then echo "DRY   $dir/$file"; continue; fi
  cp "$src/commands/$file" "$dir/$file"
  echo "OK    $dir/$file"
done
