#!/usr/bin/env python3
"""
run_ouroboros.py — Executor Mestre do Meta-Pipeline AIDD-OUROBOROS
Autor: Heverton Eduardo Peres (2026)
Padrão: AIDD Universal Architecture
"""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any, Dict


def check_doctor():
    print("=== [AIDD-OUROBOROS] Diagnostico do Ecossistema Global (Pre-voo) ===")
    tools = [
        ("git", True),
        ("python", True),
        ("ffmpeg", True),
        ("tesseract", True),
        ("yt-dlp", True),
        ("bun", False),
        ("edge-tts", False),
        ("gh", False),
    ]

    all_required_ok = True
    for tool, required in tools:
        found = shutil.which(tool)
        if not found and tool == "tesseract":
            win_default = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
            if win_default.exists():
                found = str(win_default)

        status_str = "OK" if found else ("AUSENTE (Critico)" if required else "AUSENTE (Opcional)")
        prefix = "[+]" if found else ("[!]" if required else "[-]")
        print(f"{prefix} {tool.ljust(12)}: {status_str}")
        if required and not found:
            all_required_ok = False

    if all_required_ok:
        print("\nTodos os binarios criticos do ciclo infinito estao operacionais.")
        return True
    else:
        print("\nExistem binarios essenciais ausentes. Corrija os apontamentos acima.", file=sys.stderr)
        return False


def run_audit(target_dir_str: str = "."):
    print(f"=== [AIDD-OUROBOROS] Auditoria Global de Governança Fractal: {target_dir_str} ===")
    root = Path(target_dir_str).resolve()
    if root.name == "aidd-ouroboros":
        root = root.parent

    audit_runner_path = root / "motores" / "governanca" / "audit_runner.py"
    if audit_runner_path.is_file():
        cmd = [sys.executable, str(audit_runner_path), "--skip-pytest"]
        res = subprocess.run(cmd, cwd=str(root))
        if res.returncode != 0:
            print("[!] Falha nos Quality Gates do Ouroboros.", file=sys.stderr)
            return False
        return True
    else:
        # Fallback local de micro-frontmatter
        skills_found = list(root.glob("aidd-skills/*/SKILL.md"))
        for sk in skills_found:
            content = sk.read_text(encoding="utf-8")
            if "description:" in content:
                desc_line = [l for l in content.splitlines() if l.strip().startswith("description:")][0]
                words = len(desc_line.replace("description:", "").strip().split())
                if words > 25:
                    print(f"[!] {sk.parent.name} excede 25 palavras.", file=sys.stderr)
                    return False
        return True


def dispatch_video_cycle(video_url: str):
    print(f"=== [AIDD-OUROBOROS] Despachando Ciclo Infinito a partir de Video ===")
    print(f"[*] Entrada: {video_url}")
    
    # 1. Executar dissecacao REA
    script_reengineer = Path("aidd-skills/aidd-rea-video-youtube/scripts/video_reengineer.py")
    if not script_reengineer.exists():
        script_reengineer = Path("aidd-rea-video-youtube/scripts/video_reengineer.py")
    if script_reengineer.exists():
        cmd = [sys.executable, str(script_reengineer), video_url, "--analise", "full"]
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print("[ERRO] Falha na dissecacao de video.", file=sys.stderr)
            return False
    else:
        print("[ERRO] aidd-rea-video-youtube nao localizado.", file=sys.stderr)
        return False

    print("[OK] Lobulo esquerdo de dissecacao executado com sucesso.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Executor Mestre do Meta-Pipeline AIDD-OUROBOROS (Ciclo Infinito)")
    parser.add_argument("--doctor", action="store_true", help="Diagnostico completo dos pre-requisitos do ecossistema")
    parser.add_argument("--audit", metavar="PASTA", nargs="?", const=".", help="Auditoria de conformidade e regras globais")
    parser.add_argument("--video", metavar="URL", help="Dispara o ciclo completo a partir de uma URL de video")
    parser.add_argument("--github-scout", metavar="QUERY", help="Dispara o ciclo a partir de garimpo no GitHub")

    args = parser.parse_args()

    if args.doctor:
        ok = check_doctor()
        sys.exit(0 if ok else 1)

    if args.audit is not None:
        ok = run_audit(args.audit)
        sys.exit(0 if ok else 1)

    if args.video:
        ok = dispatch_video_cycle(args.video)
        sys.exit(0 if ok else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
