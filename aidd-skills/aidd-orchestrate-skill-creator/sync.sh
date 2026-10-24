#!/usr/bin/env bash
set -euo pipefail
name="aidd-orchestrate-skill-creator"
src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
h="$HOME"

targets=(
  "$h/.agents/skills"
  "$h/.claude/skills"
  "$h/.config/opencode/skills"
  "$h/.opencode/skills"
  "$h/.gemini/skills"
  "$h/.gemini/antigravity/skills"
  "$h/.gemini/antigravity-cli/skills"
  "$h/.gemini/config/skills"
  "$h/.cursor/skills"
  "$h/.hermes/skills"
  "$h/.cline/skills"
  "$h/.factory/skills"
  "$h/.mimocode/skills"
)

for t in "${targets[@]}"; do
  if [[ ! -d "$t" && "$t" != *".agents/skills"* && "$t" != *".gemini/config/skills"* ]]; then
    echo "SKIP  $t (ausente)"
    continue
  fi
  dest="$t/$name"
  if [[ -d "$dest" && "$(cd "$dest" && pwd)" == "$src" ]]; then
    echo "SKIP  $dest (mesma fonte)"
    continue
  fi
  mkdir -p "$dest"
  cp -R "$src/"* "$dest/"
  echo "OK    $dest"
done
