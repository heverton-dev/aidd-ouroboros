"""Teste de higiene de repositório (NT-01).

Garante que arquivos de estado de pipeline, mídias pesadas (.mp4, .wav, .mp3)
e diretórios transitórios de contexto não sejam rastreados no git.
"""

from __future__ import annotations

import pathlib
import re
import subprocess


def test_no_runtime_or_heavy_media_tracked_in_git() -> None:
    repo_root = pathlib.Path(__file__).resolve().parent.parent
    allowlist_file = repo_root / "tests" / "FIXTURES_ALLOWLIST.txt"
    allowlist: set[str] = set()
    if allowlist_file.exists():
        allowlist = {
            line.strip()
            for line in allowlist_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        }

    cmd = ["git", "ls-files"]
    proc = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True, check=True)
    tracked_files = proc.stdout.splitlines()

    pattern = re.compile(
        r"(^|/)state\.json$|/context/(input|handoffs|output)/|\.(mp4|wav|mp3)$"
    )

    violations = [
        f for f in tracked_files
        if f not in allowlist
        and pattern.search(f.replace("\\", "/"))
        and not f.replace("\\", "/").endswith("/README.md")
    ]

    assert not violations, (
        f"Arquivos de runtime/mídia rastreados no git ({len(violations)} encontrados):\n"
        + "\n".join(violations)
    )
