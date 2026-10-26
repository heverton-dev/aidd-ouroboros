#!/usr/bin/env python3
"""
run_ouroboros.py — Delegador unificado do Meta-Pipeline AIDD-OUROBOROS
Autor: Heverton Eduardo Peres (2026)
Padrão: AIDD Universal Architecture

Entrypoint legado (`aidd-ouroboros/`). Toda a semântica de doctor/audit/plan
e o meta-fluxo F1/F2 vivem no entrypoint soberano `ouroboros.py` na raiz do repo.
Este arquivo apenas despacha para a raiz para não divergirem.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ROOT_CLI = REPO_ROOT / "ouroboros.py"


def _dispatch(args: List[str]) -> int:
    if not ROOT_CLI.is_file():
        print(f"[!] Entrypoint soberano ausente: {ROOT_CLI}", file=sys.stderr)
        return 1
    return subprocess.run([sys.executable, str(ROOT_CLI), *args]).returncode


def check_doctor() -> bool:
    return _dispatch(["--doctor"]) == 0


def run_audit(target_dir_str: str = ".") -> bool:
    del target_dir_str  # auditoria é sempre sobre a branch atual na raiz
    return _dispatch(["--audit"]) == 0


def dispatch_video_cycle(video_url: str) -> bool:
    """Ciclo de vídeo → REA router (canônico) na raiz."""
    router = REPO_ROOT / "aidd-skills" / "aidd-rea-router" / "scripts" / "rea_router.py"
    if not router.is_file():
        print(f"[ERRO] aidd-rea-router ausente: {router}", file=sys.stderr)
        return False
    cmd = [sys.executable, str(router), "--target", video_url]
    return subprocess.run(cmd, cwd=str(REPO_ROOT)).returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Delegador AIDD-OUROBOROS (use `ouroboros` na raiz para o CLI completo)"
    )
    parser.add_argument("--doctor", action="store_true", help="Delega para ouroboros.py --doctor")
    parser.add_argument("--audit", metavar="PASTA", nargs="?", const=".", help="Delega para ouroboros.py --audit")
    parser.add_argument("--video", metavar="URL", help="Dispara REA do alvo de vídeo via rea-router")
    parser.add_argument(
        "--from-nl",
        metavar="TEXTO",
        help="Delega F1: semeia SPEC_PIPELINE.json",
    )
    parser.add_argument(
        "--orchestrate",
        metavar="SPEC",
        help="Delega F2: orquestração autônoma",
    )
    parser.add_argument("--output-spec", metavar="CAMINHO", default=None)
    parser.add_argument("--output-dir", metavar="DIR", default=None)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    if args.doctor:
        return _dispatch(["--doctor"])

    if args.audit is not None:
        return _dispatch(["--audit"])

    if args.from_nl:
        extra: List[str] = ["--from-nl", args.from_nl]
        if args.output_spec:
            extra.extend(["--output-spec", args.output_spec])
        return _dispatch(extra)

    if args.orchestrate:
        extra = ["--orchestrate", args.orchestrate]
        if args.output_dir:
            extra.extend(["--output-dir", args.output_dir])
        if args.resume:
            extra.append("--resume")
        return _dispatch(extra)

    if args.video:
        return 0 if dispatch_video_cycle(args.video) else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
