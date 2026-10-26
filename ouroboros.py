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


def repo_root() -> Path:
    """Resolve a raiz do repositório Ouroboros (env, pacote instalado ou cwd)."""
    env = os.environ.get("AIDD_OUROBOROS_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if (p / "aidd-skills").is_dir():
            return p

    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / "aidd-skills").is_dir() and (candidate / "motores").is_dir():
            return candidate

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "aidd-skills").is_dir() and (candidate / "motores").is_dir():
            return candidate

    return here


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
    root = repo_root()
    audit_runner = root / "motores" / "governanca" / "audit_runner.py"
    if not audit_runner.is_file():
        print(f"[!] Auditor de Quality Gates não encontrado em {audit_runner}", file=sys.stderr)
        return False

    cmd = [sys.executable, str(audit_runner)]
    res = subprocess.run(cmd, cwd=str(root))
    return res.returncode == 0


def run_setup() -> bool:
    root = repo_root()
    print("=" * 70)
    print(" ⚙️  [AIDD-OUROBOROS] Setup Automático & Sincronização Multi-Harness")
    print("=" * 70)

    uv = shutil.which("uv")
    req_file = root / "requirements.txt"
    pyproject = root / "pyproject.toml"

    # 1. Instalar pacote + deps (preferir UV)
    if uv and pyproject.is_file():
        print("[*] Instalando pacote editável via uv...")
        res = subprocess.run([uv, "pip", "install", "-q", "-e", str(root)], cwd=str(root))
        if res.returncode != 0:
            print("[!] uv pip install -e falhou; tentando pip...", file=sys.stderr)
            res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "-e", str(root)],
                cwd=str(root),
            )
        if res.returncode != 0:
            print("[!] Falha ao instalar o pacote aidd-ouroboros.", file=sys.stderr)
            return False
    elif req_file.is_file():
        print("[*] Instalando dependências de requirements.txt...")
        res = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req_file)])
        if res.returncode != 0:
            print("[!] Falha ao instalar dependências Python via pip.", file=sys.stderr)
            return False

    # 2. Sincronizar skills multi-harness (mestra primeiro)
    skills_dir = root / "aidd-skills"
    if skills_dir.is_dir():
        print("[*] Sincronizando skills canônicas para harnesses do sistema...")
        masters = [skills_dir / "aidd-ouroboros-master" / "sync.ps1"]
        others = [p for p in skills_dir.glob("*/sync.ps1") if p.parent.name != "aidd-ouroboros-master"]
        for sync in masters + others:
            if not sync.is_file():
                continue
            print(f"  -> Sincronizando {sync.parent.name}...")
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(sync)], capture_output=True)

    # 3. Pré-voo + gates
    print("[*] Diagnóstico...")
    if not check_doctor():
        return False
    print("[*] Quality Gates...")
    if not run_audit():
        return False

    print("[OK] Setup concluído com sucesso.\n")
    print("[*] Uso: ouroboros --from-nl \"...\"  |  /ouroboros no harness\n")
    return True


def run_pipeline(pipeline_name: str, force: bool = False, live: bool = False) -> bool:
    root = repo_root()
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

    schema_path = repo_root() / "schemas" / "PLAN.schema.json"
    if schema_path.is_file():
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        jsonschema.validate(instance=plano, schema=schema)

    return plano


def _master_script() -> Path:
    return repo_root() / "aidd-skills" / "aidd-ouroboros-master" / "scripts" / "ouroboros_master.py"


def run_master(args: argparse.Namespace) -> int:
    """Encaminha para o orquestrador mestre (F1 semear / F2 orquestrar)."""
    script = _master_script()
    if not script.is_file():
        print(f"[!] Skill mestra ausente: {script}", file=sys.stderr)
        return 1

    if args.from_nl:
        cmd = [
            sys.executable,
            str(script),
            "--from-nl",
            args.from_nl,
            "--output-spec",
            args.output_spec or str(Path.cwd() / "SPEC_PIPELINE.json"),
        ]
        if args.goal:
            cmd.extend(["--goal", args.goal])
        return subprocess.run(cmd).returncode

    if args.orchestrate:
        cmd = [
            sys.executable,
            str(script),
            "--orchestrate",
            args.orchestrate,
            "--output-dir",
            args.output_dir or str(Path.cwd() / "ouroboros-out"),
        ]
        if args.resume:
            cmd.append("--resume")
        return subprocess.run(cmd).returncode

    if args.master_doctor:
        return subprocess.run([sys.executable, str(script), "--doctor"]).returncode

    print("[!] Use --from-nl, --orchestrate ou --master-doctor.", file=sys.stderr)
    return 1


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
  python ouroboros.py --from-nl "criar pipeline X a partir de https://y"
  python ouroboros.py --orchestrate ./SPEC_PIPELINE.json --output-dir ./ouroboros-out
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
    parser.add_argument("--from-nl", metavar="TEXTO", help="F1: semeia SPEC_PIPELINE.json a partir de pedido em linguagem natural")
    parser.add_argument("--orchestrate", metavar="SPEC", help="F2: executa orquestração autônoma a partir de SPEC_PIPELINE.json")
    parser.add_argument("--output-spec", metavar="CAMINHO", help="Caminho de saída para --from-nl (padrão: ./SPEC_PIPELINE.json)")
    parser.add_argument("--output-dir", metavar="DIR", help="Diretório de artefatos para --orchestrate (padrão: ./ouroboros-out)")
    parser.add_argument("--resume", action="store_true", help="Retoma state da orquestração após mini-entrevista")
    parser.add_argument("--master-doctor", action="store_true", help="Diagnóstico da skill mestra aidd-ouroboros-master")

    args = parser.parse_args()

    if args.from_nl or args.orchestrate or args.master_doctor:
        sys.exit(run_master(args))

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
