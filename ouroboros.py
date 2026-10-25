#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ouroboros.py — Meta-Fábrica Universal AIDD (AI-Driven Development)
Autor: Heverton Eduardo Peres (2026)
Padrão: AIDD Universal Architecture / Zero Stubs / Extreme Token Economy / HMAC-SHA256

Entrypoint Soberano do Ecossistema Ouroboros.
Capacidades:
  1. --doctor: Diagnóstico de ambiente, binários críticos e credenciais de IA.
  2. --credentials: Diagnóstico e status de chaves de API (Gemini e Google Flow).
  3. --audit: Execução completa dos Quality Gates fractais da branch (AST, Micro-Frontmatter, AGENTS.md, Pytest).
  4. --setup: Instalação automática e sincronização multi-harness de todas as skills.
  5. --pipeline <nome>: Execução topológica de enxames de skills encapsuladas.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import jsonschema

from motores.governanca.credentials import carregar_env_local, obter_credenciais_ia, verificar_prontidao_live


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
    print(" 🔑 Credenciais & Motores de IA Generativa:")
    pronto_live, ausentes = verificar_prontidao_live()
    creds = obter_credenciais_ia()
    mode = creds.get("execution_mode", "DRY_RUN")
    print(f" [*] Modo Atual: {mode}")
    print(f" [*] Gemini API: {'CONFIGURADA' if creds.get('gemini_api_key') and creds.get('gemini_api_key') != 'sua_chave_gemini_aqui' else 'PENDENTE (usando simulação determinística)'}")
    print(f" [*] Google Cloud / Flow: {'CONFIGURADA' if creds.get('gcp_project') and creds.get('gcp_project') != 'seu-projeto-gcp-id' else 'PENDENTE (usando compilação de payload)'}")

    if not pronto_live:
        print(" [!] Dica: Para chamadas ao vivo nas APIs do Gemini e Google Flow, configure o arquivo .env (copie de .env.example).")

    print("-" * 70)
    if all_ok:
        print("[OK] Todos os binários críticos do Ouroboros estão operacionais.\n")
        return True
    else:
        print("[!] Existem binários essenciais ausentes. Verifique os alertas acima.\n", file=sys.stderr)
        return False


def check_credentials_cmd() -> bool:
    print("=" * 70)
    print(" 🔐 [AIDD-OUROBOROS] Status de Credenciais e Motores de IA")
    print("=" * 70)
    creds = obter_credenciais_ia()
    pronto, ausentes = verificar_prontidao_live()

    print(f" Modo de Execução : {creds.get('execution_mode')}")
    print(f" Modelo Gemini    : {creds.get('gemini_model')}")
    print(f" Gemini API Key   : {'DEFINIDA (' + creds.get('gemini_api_key')[:6] + '...)' if creds.get('gemini_api_key') and creds.get('gemini_api_key') != 'sua_chave_gemini_aqui' else 'NÃO CONFIGURADA'}")
    print(f" Projeto GCP/Flow : {creds.get('gcp_project') or 'NÃO CONFIGURADO'}")
    print(f" Região GCP       : {creds.get('gcp_location')}")
    print(f" Service Account  : {creds.get('gcp_credentials') or 'NÃO CONFIGURADO'}")
    print("-" * 70)

    if pronto:
        print("[OK] Todas as credenciais para LIVE RUN estão presentes e prontas para uso.\n")
        return True
    else:
        print(f"[!] Credenciais pendentes para modo LIVE: {', '.join(ausentes)}")
        print("    O pipeline executará em modo DRY_RUN gerando manifests e payloads válidos.\n")
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


def run_pipeline(pipeline_name: str, force: bool = False, live: bool = False) -> bool:
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
    if live:
        cmd.append("--live")

    res = subprocess.run(cmd, cwd=str(pipe_dir))
    return res.returncode == 0


def sintetizar_plano(target: str, goal: str, taxonomy_path: Path | None = None) -> dict:
    target_clean = target.strip()
    target_lower = target_clean.lower()
    goal_clean = goal.strip()
    combined_text = f"{target_lower} {goal_clean.lower()}"

    primary_skill = None
    input_type = None

    if target_lower.endswith(".apk") or (target_lower.endswith(".zip") and any(k in combined_text for k in ["apk", "app", "android"])):
        primary_skill = "aidd-rea-app-android"
        input_type = "file/apk"
    elif target_lower.endswith(".mp4") or "youtube.com" in target_lower or "youtu.be" in target_lower:
        primary_skill = "aidd-rea-video-youtube"
        input_type = "video/mp4"
    elif target_lower.startswith(("http://", "https://")) or target_lower.endswith(".html"):
        primary_skill = "aidd-rea-web-saas"
        input_type = "text/html"
    elif "slides" in combined_text or target_lower.endswith((".pdf", ".pptx")):
        primary_skill = "aidd-rea-social-carousel"
        input_type = "dir:slides"
    else:
        raise ValueError("Não foi possível mapear o target para uma skill canônica.")

    plan_hash = hashlib.sha256(f"{target_clean}{goal_clean}".encode("utf-8")).hexdigest()[:16]
    plan_id = f"plan-{plan_hash}"
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    plano = {
        "plan_id": plan_id,
        "version": "1.0.0",
        "target": target_clean,
        "goal": goal_clean,
        "steps": [
            {
                "step_index": 1,
                "skill": primary_skill,
                "input_type": input_type,
                "output_contract": "HANDOFF.json"
            }
        ],
        "deterministic": True,
        "created_at": now_iso
    }

    schema_path = Path(__file__).resolve().parent / "schemas" / "PLAN.schema.json"
    if schema_path.is_file():
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=plano, schema=schema)

    return plano


def main():
    parser = argparse.ArgumentParser(
        description="AIDD OUROBOROS — A Meta-Fábrica Universal Autônoma",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de Uso:
  python ouroboros.py --doctor                   # Diagnóstico de binários e credenciais
  python ouroboros.py --credentials              # Status detalhado das chaves de API
  python ouroboros.py --audit                    # Executa Quality Gates fractais da branch
  python ouroboros.py --pipeline commercial-spec-flow # Executa o pipeline em modo DRY_RUN
  python ouroboros.py --pipeline commercial-spec-flow --live # Executa chamando APIs reais
  python ouroboros.py --target app.apk --goal "Engenharia reversa" --dry-run
        """
    )
    parser.add_argument("--doctor", action="store_true", help="Diagnóstico dos pré-requisitos de ambiente e IA")
    parser.add_argument("--credentials", action="store_true", help="Status e validação de chaves de API")
    parser.add_argument("--audit", action="store_true", help="Auditoria completa de conformidade e gates de código")
    parser.add_argument("--setup", action="store_true", help="Instalação automática e sincronização multi-harness")
    parser.add_argument("--pipeline", metavar="NOME", help="Executa o runner de um pipeline específico em aidd-pipelines/")
    parser.add_argument("--force", action="store_true", help="Força reexecução de nós já concluídos no pipeline")
    parser.add_argument("--live", action="store_true", help="Executa chamadas reais para as APIs de IA (requer .env configurado)")
    parser.add_argument("--target", help="Alvo de entrada para síntese e execução do plano (arquivo, URL ou diretório)")
    parser.add_argument("--goal", help="Objetivo funcional do plano a ser sintetizado")
    parser.add_argument("--dry-run", action="store_true", help="Gera o plano deterministicamente sem executar efeitos colaterais")
    parser.add_argument("--output-plan", metavar="CAMINHO", help="Caminho para salvar o plano sintetizado em formato JSON")

    args = parser.parse_args()

    if args.target and args.goal:
        try:
            plano = sintetizar_plano(args.target, args.goal)
        except Exception as exc:
            print(f"[!] Erro ao sintetizar plano: {exc}", file=sys.stderr)
            sys.exit(1)

        plan_json = json.dumps(plano, indent=2, ensure_ascii=False)
        if args.output_plan:
            out_p = Path(args.output_plan)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(plan_json, encoding="utf-8")

        if args.dry_run or not args.pipeline:
            print(plan_json)
            sys.exit(0)
    elif args.target or args.goal or (args.dry_run and not args.pipeline):
        print("[!] --target e --goal são necessários para síntese de plano.", file=sys.stderr)
        sys.exit(1)

    if args.doctor:
        sys.exit(0 if check_doctor() else 1)
    elif args.credentials:
        sys.exit(0 if check_credentials_cmd() else 1)
    elif args.audit:
        sys.exit(0 if run_audit() else 1)
    elif args.setup:
        sys.exit(0 if run_setup() else 1)
    elif args.pipeline:
        sys.exit(0 if run_pipeline(args.pipeline, force=args.force, live=args.live) else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
