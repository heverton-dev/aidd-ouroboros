#!/usr/bin/env bash
set -euo pipefail
name="aidd-rea-router"
src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
h="$HOME"
targets=("$h/.agents/skills" "$h/.claude/skills" "$h/.gemini/config/skills" "$h/.cursor/skills" "$h/.hermes/skills")
for t in "${targets[@]}"; do
  mkdir -p "$t/$name"
  cp -R "$src/"* "$t/$name/"
  echo "OK $t/$name"
done
