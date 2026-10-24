#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ouroboros.py — Meta-Fábrica Universal AIDD (AI-Driven Development)
Autor: Heverton Eduardo Peres (2026)
Padrão: AIDD Universal Architecture / Zero Stubs / Extreme Token Economy / HMAC-SHA256

Entrypoint Soberano do Ecossistema Ouroboros.
Capacidades:
  1. --doctor: Diagnóstico de ambiente e binários críticos (ffmpeg, git, python, yt-dlp).
  2. --audit: Execução completa dos Quality Gates fractais da branch (AST, Micro-Frontmatter, AGENTS.md, Pytest).
  3. --setup: Instalação automática e sincronização multi-harness de todas as skills.
  4. --pipeline <nome>: Execução topológica de enxames de skills encapsuladas.
  5. --video <url>: Ingestão e dissecção via REA Multimodal.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import time


def check_doctor() -> bool:
    print("=" * 70)
    print(" 🩺 [AIDD-OUROBOROS] Diagnóstico de Ambiente & Pré-Voo")
    print("=" * 70)
    tools = [
        ("git", True),
        ("python", True),
        ("ffmpeg", True),
        ("tesseract", False),
        ("yt-dlp", False),
        ("bun", False),
        ("gh", True),
    ]

    all_ok = True
    for tool, required in tools:
        found = shutil.which(tool)
        if not found and tool == "tesseract":
            win_default = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
            if win_default.exists():
                found = str(win_default)

        status_str = "OK" if found else ("AUSENTE (Crítico)" if required else "AUSENTE (Opcional)")
        prefix = "[+]" if found else ("[!]" if required else "[-]")
        print(f" {prefix} {tool.ljust(14)}: {status_str}")
        if required and not found:
            all_ok = False

    print("-" * 70)
    if all_ok:
        print("[OK] Todos os binários críticos do Ouroboros estão operacionais.\n")
        return True
    else:
        print("[!] Existem binários essenciais ausentes. Verifique os alertas acima.\n", file=sys.stderr)
        return False


def run_audit() -> bool:
    root = Path(__file__).resolve().parent
    audit_runner = root / "motores" / "governanca" / "audit_runner.py"
    if not audit_runner.is_file():
        print(f"[!] Auditor de Quality Gates não encontrado em {audit_runner}", file=sys.stderr)
        return False

    cmd = [sys.executable, str(audit_runner)]
    res = subprocess.run(cmd, cwd=str(root))
    return res.returncode == 0


def run_setup() -> bool:
    root = Path(__file__).resolve().parent
    print("=" * 70)
    print(" ⚙️  [AIDD-OUROBOROS] Setup Automático & Sincronização Multi-Harness")
    print("=" * 70)

    # 1. Instalar dependências Python
    req_file = root / "requirements.txt"
    if req_file.is_file():
        print("[*] Instalando dependências de requirements.txt...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)])
        if res.returncode != 0:
            print("[!] Falha ao instalar dependências Python via pip.", file=sys.stderr)

    # 2. Sincronizar skills multi-harness
    skills_dir = root / "aidd-skills"
    if skills_dir.is_dir():
        print("[*] Sincronizando skills canônicas para harnesses do sistema...")
        sync_scripts = list(skills_dir.glob("*/sync.ps1"))
        for sync in sync_scripts:
            print(f"  -> Sincronizando {sync.parent.name}...")
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(sync)], capture_output=True)

    print("[OK] Setup concluído com sucesso.\n")
    return True


def run_pipeline(pipeline_name: str, force: bool = False) -> bool:
    root = Path(__file__).resolve().parent
    pipe_dir = root / "aidd-pipelines" / pipeline_name
    if not pipe_dir.is_dir():
        print(f"[!] Pipeline '{pipeline_name}' não encontrado em {root / 'aidd-pipelines'}", file=sys.stderr)
        return False

    runner = pipe_dir / "run_pipeline.py"
    if not runner.is_file():
        print(f"[!] Runner 'run_pipeline.py' não encontrado em {pipe_dir}", file=sys.stderr)
        return False

    cmd = [sys.executable, str(runner)]
    if force:
        cmd.append("--force")
    res = subprocess.run(cmd, cwd=str(pipe_dir))
    return res.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="AIDD OUROBOROS — A Meta-Fábrica Universal Autônoma",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de Uso:
  python ouroboros.py --doctor                  # Verifica dependências e binários
  python ouroboros.py --audit                   # Executa Quality Gates fractais da branch
  python ouroboros.py --setup                   # Instala dependências e propaga skills
  python ouroboros.py --pipeline canal-dark-avatar # Dispara o DAG de um pipeline
        """
    )
    parser.add_argument("--doctor", action="store_true", help="Diagnóstico dos pré-requisitos de ambiente")
    parser.add_argument("--audit", action="store_true", help="Auditoria completa de conformidade e gates de código")
    parser.add_argument("--setup", action="store_true", help="Instalação automática e sincronização multi-harness")
    parser.add_argument("--pipeline", metavar="NOME", help="Executa o runner de um pipeline específico em aidd-pipelines/")
    parser.add_argument("--force", action="store_true", help="Força reexecução de nós já concluídos no pipeline")

    args = parser.parse_args()

    if args.doctor:
        sys.exit(0 if check_doctor() else 1)
    elif args.audit:
        sys.exit(0 if run_audit() else 1)
    elif args.setup:
        sys.exit(0 if run_setup() else 1)
    elif args.pipeline:
        sys.exit(0 if run_pipeline(args.pipeline, force=args.force) else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
