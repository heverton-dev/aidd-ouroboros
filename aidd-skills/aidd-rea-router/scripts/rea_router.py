#!/usr/bin/env python3
"""
rea_router.py — Roteador Universal e Classificador de Alvos REA (aidd-rea-router)
Autor: Heverton Eduardo Peres (2026)
Padrão: AIDD / REA + aidd-lauren

Capacidades Enterprise:
1. --target <INPUT> / --route <INPUT>: Classifica a mídia e despacha a dissecação para a micro-skill especialista.
2. --classify <INPUT>: Apenas classifica o alvo sem executar o dissecador.
3. --output-handoff <CAMINHO>: Emissão do envelope universal de handoff interoperável.
4. --doctor: Diagnóstico de ambiente e conectividade com as micro-skills REA.
5. --setup: Setup automático e sincronização.
6. --audit: Auditor de conformidade dos 4 Gates com Circuit Breaker.
"""

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_AUTHOR = "Heverton Eduardo Peres"


def time_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w-]+\b", text))


def extract_frontmatter_description(skill_md_path: Path) -> str:
    content = skill_md_path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return ""
    frontmatter = match.group(1)
    desc_match = re.search(r"^description:\s*(.*?)$", frontmatter, re.MULTILINE)
    if desc_match:
        return desc_match.group(1).strip()
    return ""


def check_doctor() -> bool:
    print("=== [AIDD-REA-ROUTER] Diagnostico de Ambiente (Doctor) ===")
    py_ver = sys.version.split()[0]
    print(f"[+] Python: {py_ver} (OK)")

    git_path = shutil.which("git")
    if git_path:
        print(f"[+] git: instalado em {git_path} (OK)")
    else:
        print(f"[!] git: NAO ENCONTRADO.")

    # Validar presença das 4 micro-skills especialistas no Almoxarifado
    root = Path(__file__).resolve().parent.parent.parent
    specialists = [
        "aidd-rea-video-youtube",
        "aidd-rea-web-saas",
        "aidd-rea-social-carousel",
        "aidd-rea-app-android"
    ]
    all_ok = True
    for sp in specialists:
        sp_dir = root / sp
        if sp_dir.exists() and (sp_dir / "SKILL.md").exists():
            print(f"[+] Especialista {sp}: OK no Almoxarifado")
        else:
            print(f"[-] Especialista {sp}: NAO ENCONTRADO em {sp_dir}")
            all_ok = False

    if all_ok:
        print("\nTodos os 4 dissecadores especialistas estao conectados e operacionais!")
    return True


def run_setup() -> bool:
    print("=== [AIDD-REA-ROUTER] Executando Setup Automatico ===")
    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    req_file = skill_root / "requirements.txt"

    uv_path = shutil.which("uv")
    if uv_path and req_file.exists():
        subprocess.run([uv_path, "pip", "install", "-r", str(req_file)], check=True)
    elif req_file.exists():
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], check=True)

    if os.name == "nt":
        sync_script = skill_root / "sync.ps1"
        if sync_script.exists():
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(sync_script)], check=True)
    else:
        sync_script = skill_root / "sync.sh"
        if sync_script.exists():
            subprocess.run(["bash", str(sync_script)], check=True)

    print("\n[OK] aidd-rea-router sincronizada e operacional!")
    return True


def run_audit(target_dir_str: str) -> bool:
    print(f"=== [AIDD-CIRCUIT-BREAKER] Auditando Roteador REA: {target_dir_str} ===")
    target_dir = Path(target_dir_str)
    if not target_dir.exists():
        print(f"[FALHA] Diretorio nao encontrado: {target_dir}", file=sys.stderr)
        sys.exit(1)

    errors = []

    # GATE 1: Micro-Frontmatter
    print("[*] Validando GATE 1 (Micro-Frontmatter <= 25 palavras no System Prompt)...")
    skill_md = target_dir / "SKILL.md"
    if not skill_md.exists():
        errors.append("GATE 1 FALHOU: Arquivo 'SKILL.md' ausente.")
    else:
        desc = extract_frontmatter_description(skill_md)
        w_count = count_words(desc)
        if not desc or w_count > 25:
            errors.append(f"GATE 1 FALHOU: Descricao com {w_count} palavras (limite: 25).")
        else:
            print(f"    [OK] Micro-Frontmatter validado: {w_count} palavras (limite: 25).")

    # GATE 2: Dual-Spec
    print("[*] Validando GATE 2 (Dual-Spec: SKILL.md + AGENTS.md)...")
    if not (target_dir / "AGENTS.md").exists():
        errors.append("GATE 2 FALHOU: 'AGENTS.md' ausente.")
    else:
        print("    [OK] Dual-Spec validado: SKILL.md e AGENTS.md presentes.")

    # GATE 3: Governança Enterprise
    print("[*] Validando GATE 3 (Governanca: RULES, LICENSE, pyproject, dependencies, sync)...")
    req_files = ["RULES.md", "LICENSE", "pyproject.toml", "requirements.txt", "dependencies.json", "README.md"]
    for rf in req_files:
        if not (target_dir / rf).exists():
            errors.append(f"GATE 3 FALHOU: Arquivo '{rf}' ausente.")

    if not (target_dir / "sync.ps1").exists() and not (target_dir / "sync.sh").exists():
        errors.append("GATE 3 FALHOU: Scripts de sincronizacao ausentes.")

    # GATE 4: Script Executável e Flags Obrigatórias
    print("[*] Validando GATE 4 (Capacidades nos Scripts)...")
    scripts = list((target_dir / "scripts").glob("*.py"))
    if not scripts:
        errors.append("GATE 4 FALHOU: Nenhum script em 'scripts/'.")
    else:
        s_code = scripts[0].read_text(encoding="utf-8")
        if "--doctor" not in s_code:
            errors.append("GATE 4 FALHOU: Script nao implementa '--doctor'.")
        if "--audit" not in s_code:
            errors.append("GATE 4 FALHOU: Script nao implementa '--audit'.")
        if "--classify" not in s_code:
            errors.append("GATE 4 FALHOU: Script nao implementa '--classify'.")

    if errors:
        print("\n[!] CIRCUIT BREAKER DESARMADO:", file=sys.stderr)
        for err in errors:
            print(f"  [-] {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n[OK] Todos os 4 Gates do Roteador REA passaram com sucesso!")
        return True


def classify_target(target: str) -> dict:
    """
    Classifica deterministicamente a natureza da entrada:
    - video: YouTube, TikTok, Reels, MP4, MKV
    - web: URL HTTP/HTTPS tradicional, SaaS
    - social: Carrossel, imagens de slides, posts de redes
    - app: APK Android, executáveis ou binários
    """
    target_clean = target.strip()
    target_lower = target_clean.lower()

    # 1. Checagem de Vídeo por URL ou Extensão
    video_domains = ["youtube.com", "youtu.be", "tiktok.com", "instagram.com/reel", "vimeo.com"]
    video_exts = [".mp4", ".mkv", ".mov", ".webm", ".avi"]
    if any(d in target_lower for d in video_domains) or any(target_lower.endswith(ext) for ext in video_exts):
        return {
            "type": "video",
            "skill": "aidd-rea-video-youtube",
            "script": "video_reengineer.py",
            "confidence": 1.0,
            "reason": "Dominio ou extensao de midia audiovisual identificada."
        }

    # 2. Checagem de Web App / SaaS
    if target_lower.startswith("http://") or target_lower.startswith("https://"):
        return {
            "type": "web",
            "skill": "aidd-rea-web-saas",
            "script": "web_reengineer.py",
            "confidence": 1.0,
            "reason": "URL de protocolo web HTTP/HTTPS detectada."
        }

    # 3. Checagem de Aplicativo / Binário
    app_exts = [".apk", ".aab", ".exe", ".msi", ".elf", ".bin"]
    if any(target_lower.endswith(ext) for ext in app_exts):
        return {
            "type": "app",
            "skill": "aidd-rea-app-android",
            "script": "app_reengineer.py",
            "confidence": 1.0,
            "reason": "Extensao de pacote mobile ou binario executavel detectada."
        }

    # 4. Checagem de Diretório / Social
    p = Path(target_clean)
    if p.is_dir():
        image_exts = {".png", ".jpg", ".jpeg", ".webp"}
        files = list(p.iterdir())
        images = [f for f in files if f.suffix.lower() in image_exts]
        if images:
            return {
                "type": "social",
                "skill": "aidd-rea-social-carousel",
                "script": "social_reengineer.py",
                "confidence": 0.95,
                "reason": f"Pasta com {len(images)} imagens/slides de carrossel detectada."
            }
        # Se contiver AndroidManifest.xml
        if (p / "AndroidManifest.xml").exists() or (p / "classes.dex").exists():
            return {
                "type": "app",
                "skill": "aidd-rea-app-android",
                "script": "app_reengineer.py",
                "confidence": 1.0,
                "reason": "Estrutura descompactada de aplicativo Android detectada."
            }

    if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
        return {
            "type": "social",
            "skill": "aidd-rea-social-carousel",
            "script": "social_reengineer.py",
            "confidence": 0.9,
            "reason": "Arquivo de imagem estatica / slide de post detectado."
        }

    # Fallback inteligente
    return {
        "type": "web",
        "skill": "aidd-rea-web-saas",
        "script": "web_reengineer.py",
        "confidence": 0.5,
        "reason": "Classificacao padrão para alvo de navegacao."
    }


def route_and_execute(target: str, output_dir: Path | None = None, output_handoff: Path | None = None) -> bool:
    """
    Classifica a entrada e dispara o dissecador especialista correto no Almoxarifado Central.
    """
    classification = classify_target(target)
    media_type = classification["type"]
    specialist_skill = classification["skill"]
    script_name = classification["script"]

    print(f"=== [AIDD-REA-ROUTER] Roteando Alvo: '{target}' ===")
    print(f"[+] Classificacao: {media_type.upper()} ({classification['reason']})")
    print(f"[+] Especialista Selecionado: {specialist_skill}")

    root = Path(__file__).resolve().parent.parent.parent
    specialist_dir = root / specialist_skill
    script_path = specialist_dir / "scripts" / script_name

    if not script_path.exists():
        print(f"[ERRO] Script do especialista nao encontrado em: {script_path}", file=sys.stderr)
        return False

    out_d = output_dir or Path(f"research/{media_type}-target")
    handoff_p = output_handoff or (out_d / "HANDOFF.json")

    # Montar comando com base no especialista
    cmd = [sys.executable, str(script_path)]
    if media_type == "video":
        cmd.extend([target, "--output-handoff", str(handoff_p)])
    elif media_type == "web":
        cmd.extend([target, "--output-dir", str(out_d), "--output-handoff", str(handoff_p)])
    elif media_type == "social":
        cmd.extend(["--input", target, "--output-dir", str(out_d), "--output-handoff", str(handoff_p)])
    elif media_type == "app":
        cmd.extend(["--input", target, "--output-dir", str(out_d), "--output-handoff", str(handoff_p)])

    print(f"[*] Disparando subprocesso: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(specialist_dir))
    if res.returncode != 0:
        print(f"[ERRO] O especialista {specialist_skill} falhou com codigo {res.returncode}.", file=sys.stderr)
        return False

    print(f"\n[OK] Roteamento e dissecação concluidos com sucesso via {specialist_skill}!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Roteador Universal de Engenharia Reversa (aidd-rea-router v1.0.0)")
    parser.add_argument("target_pos", nargs="?", help="Entrada para dissecação (URL, arquivo ou pasta)")
    parser.add_argument("-i", "--input", dest="input_opt", help="Entrada para dissecação (contrato CLI padrao)")
    parser.add_argument("--target", dest="target_opt", help="Alias para o alvo de dissecação")
    parser.add_argument("--route", dest="route_opt", help="Alias para roteamento")
    parser.add_argument("--classify", metavar="INPUT", help="Apenas classifica o tipo de mídia sem executar")
    parser.add_argument("--output-dir", help="Pasta de saída para os artefatos REA")
    parser.add_argument("--output-handoff", help="Caminho customizado para emitir o HANDOFF.json")
    parser.add_argument("--doctor", action="store_true", help="Diagnostico de ambiente")
    parser.add_argument("--setup", action="store_true", help="Setup automatico e sync")
    parser.add_argument("--audit", metavar="PASTA", nargs="?", const=".", help="Auditoria dos 4 Gates com Circuit Breaker")

    args = parser.parse_args()

    if args.doctor:
        check_doctor()
        return

    if args.setup:
        run_setup()
        return

    if args.audit is not None:
        run_audit(args.audit)
        return

    if args.classify:
        result = classify_target(args.classify)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    chosen_target = args.input_opt or args.target_pos or args.target_opt or args.route_opt
    if chosen_target:
        out_d = Path(args.output_dir) if args.output_dir else None
        handoff_p = Path(args.output_handoff) if args.output_handoff else None
        ok = route_and_execute(chosen_target, output_dir=out_d, output_handoff=handoff_p)
        sys.exit(0 if ok else 1)

    parser.print_help()


if __name__ == "__main__":
    main()
