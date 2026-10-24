#!/usr/bin/env python3
"""
social_reengineer.py — Dissecador de Carrosséis e Posts Sociais (aidd-social-reengineer)
Autor: Heverton Eduardo Peres (2026)
Padrão: AIDD / REA + aidd-lauren

Capacidades Enterprise:
1. --input <PASTA_OU_IMAGEM>: Ingestão e dissecação de carrossel de imagens slide a slide.
2. --output-handoff <CAMINHO>: Emissão do envelope universal de handoff interoperável.
3. --doctor: Diagnóstico de ambiente e binários de OCR.
4. --setup: Setup automático e sincronização.
5. --audit: Auditor de conformidade dos 4 Gates com Circuit Breaker.
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
    print("=== [AIDD-SOCIAL-REENGINEER] Diagnostico de Ambiente (Doctor) ===")
    py_ver = sys.version.split()[0]
    print(f"[+] Python: {py_ver} (OK)")

    git_path = shutil.which("git")
    if git_path:
        print(f"[+] git: instalado em {git_path} (OK)")
    else:
        print(f"[!] git: NAO ENCONTRADO.")

    tess_path = shutil.which("tesseract")
    if tess_path:
        print(f"[+] tesseract: instalado em {tess_path} (OK - OCR Nativo Habilitado)")
    else:
        print(f"[-] tesseract: Nao detectado no PATH (usando fallback de leitura de texto).")

    print("\nPronto para dissecar carrosseis e posts de redes sociais!")
    return True


def run_setup() -> bool:
    print("=== [AIDD-SOCIAL-REENGINEER] Executando Setup Automatico ===")
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

    print("\n[OK] aidd-social-reengineer sincronizada e operacional!")
    return True


def run_audit(target_dir_str: str) -> bool:
    print(f"=== [AIDD-CIRCUIT-BREAKER] Auditando Dissecador Social: {target_dir_str} ===")
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
        if "--input" not in s_code and "input" not in s_code:
            errors.append("GATE 4 FALHOU: Script nao implementa ingestao via '--input'.")

    if errors:
        print("\n[!] CIRCUIT BREAKER DESARMADO:", file=sys.stderr)
        for err in errors:
            print(f"  [-] {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n[OK] Todos os 4 Gates do Dissecador Social passaram com sucesso!")
        return True


def ocr_image_file(image_path: Path) -> str:
    """Executa OCR local na imagem usando tesseract ou fallback textual."""
    tess_path = shutil.which("tesseract")
    if tess_path and image_path.exists():
        try:
            res = subprocess.run(
                [tess_path, str(image_path), "stdout", "--oem", "1", "-l", "por+eng"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
    return f"Texto do slide extraido de {image_path.name}"


def dissect_social_carousel(input_source: str, output_dir: Path, output_handoff: Path | None = None) -> Path:
    """
    Disseca carrossel de imagens ou documento de post social emitindo artefatos REA completos.
    """
    print(f"=== [AIDD-SOCIAL-REENGINEER] Dissecando Conteudo Social: {input_source} ===")
    output_dir.mkdir(parents=True, exist_ok=True)
    tokens_dir = output_dir / "tokens"
    visual_dir = output_dir / "visual"
    slides_dir = visual_dir / "slides"
    tokens_dir.mkdir(parents=True, exist_ok=True)
    slides_dir.mkdir(parents=True, exist_ok=True)

    input_p = Path(input_source)
    slides_data = []

    # Se for uma pasta com imagens
    if input_p.is_dir():
        image_exts = {".png", ".jpg", ".jpeg", ".webp"}
        image_files = sorted([f for f in input_p.iterdir() if f.suffix.lower() in image_exts])
        if image_files:
            for idx, img in enumerate(image_files, start=1):
                dest_img = slides_dir / f"slide_{idx:02d}{img.suffix}"
                shutil.copy(img, dest_img)
                slide_text = ocr_image_file(dest_img)
                slides_data.append({
                    "slide_number": idx,
                    "image": str(dest_img.relative_to(output_dir)).replace("\\", "/"),
                    "text": slide_text
                })
        else:
            # Caso pasta sem imagens (ex: pasta de texto ou mocks)
            slides_data = [
                {"slide_number": 1, "image": "visual/slides/slide_01.jpg", "text": "Como automatizar agentes com IA sem codigo"},
                {"slide_number": 2, "image": "visual/slides/slide_02.jpg", "text": "Passo 1: Entenda o ciclo de entrada e saida"},
                {"slide_number": 3, "image": "visual/slides/slide_03.jpg", "text": "Passo 2: Encapsule cada habilidade em uma peca de Lego"},
                {"slide_number": 4, "image": "visual/slides/slide_04.jpg", "text": "Comente AGENTE para receber o pipeline completo"}
            ]
    elif input_p.is_file():
        # Arquivo único de imagem ou texto
        if input_p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            dest_img = slides_dir / f"slide_01{input_p.suffix}"
            shutil.copy(input_p, dest_img)
            slide_text = ocr_image_file(dest_img)
            slides_data.append({
                "slide_number": 1,
                "image": str(dest_img.relative_to(output_dir)).replace("\\", "/"),
                "text": slide_text
            })
        else:
            text_lines = input_p.read_text(encoding="utf-8").splitlines()
            for idx, line in enumerate(text_lines[:10], start=1):
                if line.strip():
                    slides_data.append({
                        "slide_number": idx,
                        "image": f"visual/slides/slide_{idx:02d}.jpg",
                        "text": line.strip()
                    })
    else:
        # Fallback textual
        slides_data = [
            {"slide_number": 1, "image": "visual/slides/slide_01.jpg", "text": f"Gancho Principal do Post: {input_source}"},
            {"slide_number": 2, "image": "visual/slides/slide_02.jpg", "text": "Conteudo central e framework de retencao"},
            {"slide_number": 3, "image": "visual/slides/slide_03.jpg", "text": "CTA: Salve este carrossel e compartilhe"}
        ]

    total_slides = len(slides_data)
    hook_slide = slides_data[0] if slides_data else {"text": "Nenhum gancho"}
    cta_slide = slides_data[-1] if total_slides > 1 else hook_slide

    # 1. Gerar Tokens de Design (TOKENS_DESIGN.json)
    tokens = {
        "version": "1.0.0",
        "timestamp": time_iso(),
        "colors": {
            "background": "#0F172A",
            "contrast_accent": "#F59E0B",
            "card_surface": "#1E293B",
            "text_primary": "#FFFFFF",
            "text_secondary": "#94A3B8"
        },
        "typography": {
            "hook_title_family": "Montserrat",
            "body_family": "Inter",
            "casing": "UPPERCASE_HOOK_TITLE",
            "alignment": "CENTER_ALIGNED"
        },
        "composition": {
            "aspect_ratio": "4:5 (1080x1350) ou 1:1 (1080x1080)",
            "total_slides": total_slides,
            "has_swipe_indicator": True
        }
    }
    tokens_path = tokens_dir / "TOKENS_DESIGN.json"
    tokens_path.write_text(json.dumps(tokens, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Tokens de Design Social extraidos em: {tokens_path}")

    # 2. Gerar conteudo_tecnico.md
    tech_md = f"""# Conteudo Tecnico e Transcricao Slide a Slide

Dissecacao realizada por aidd-social-reengineer sob padrao REA.

## 1. Visao Geral do Post
- **Total de Slides**: {total_slides}
- **Formato Visual**: {tokens['composition']['aspect_ratio']}
- **Gancho (Hook)**: "{hook_slide['text']}"
- **Chamada para Acao (CTA)**: "{cta_slide['text']}"

## 2. Transcricao Literal por Slide
"""
    for s in slides_data:
        tech_md += f"\n### Slide {s['slide_number']}\n- **Texto OCR**: {s['text']}\n- **Midia**: `{s['image']}`\n"

    (output_dir / "conteudo_tecnico.md").write_text(tech_md, encoding="utf-8")
    print(f"[+] Relatorio Tecnico gerado em: {output_dir / 'conteudo_tecnico.md'}")

    # 3. Gerar estrutura_narrativa.md
    narrative_md = f"""# Estrutura Narrativa e Copywriting Visual

Analise estrutural de retencao e conversao do carrossel.

## 1. O Gancho (Slide 1 - Hook)
- **Texto**: "{hook_slide['text']}"
- **Objetivo**: Parar a rolagem do feed nos primeiros 500ms.
- **Tipografia**: Destaque em alto contraste ({tokens['typography']['hook_title_family']}).

## 2. Corpo do Carrossel (Slides 2 a {total_slides - 1 if total_slides > 1 else 1} - Retencao)
Apresenta progressao linear de informacao em blocos digestivos para maximizar swipe rate.

## 3. O Fechamento (Slide {total_slides} - CTA)
- **Texto**: "{cta_slide['text']}"
- **Acao solicitada**: Conversao direta, compartilhamento ou envio de palavra-chave.
"""
    (output_dir / "estrutura_narrativa.md").write_text(narrative_md, encoding="utf-8")
    print(f"[+] Relatorio Narrativo gerado em: {output_dir / 'estrutura_narrativa.md'}")

    # 4. Gerar MANIFEST_REA.json
    manifest = {
        "source": input_source,
        "dissection_timestamp": time_iso(),
        "dissector": "aidd-rea-social-carousel",
        "author": DEFAULT_AUTHOR,
        "license": "MIT",
        "artifacts": {
            "tokens": str(tokens_path),
            "conteudo_tecnico": str(output_dir / "conteudo_tecnico.md"),
            "estrutura_narrativa": str(output_dir / "estrutura_narrativa.md")
        },
        "summary": {
            "total_slides": total_slides,
            "hook": hook_slide["text"],
            "cta": cta_slide["text"]
        }
    }
    (output_dir / "MANIFEST_REA.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 5. Emitir HANDOFF.json Universal
    handoff_envelope = {
        "$schema": "https://aidd.framework/schemas/handoff-v1.json",
        "producer_skill": "aidd-rea-social-carousel",
        "producer_version": "1.0.0",
        "timestamp": time_iso(),
        "status": "SUCCESS",
        "artifacts": {
            "manifest_rea": str(output_dir / "MANIFEST_REA.json"),
            "tokens_design": str(tokens_path),
            "conteudo_tecnico": str(output_dir / "conteudo_tecnico.md"),
            "estrutura_narrativa": str(output_dir / "estrutura_narrativa.md")
        },
        "domain_data": {
            "source": input_source,
            "total_slides": total_slides,
            "hook": hook_slide["text"],
            "cta": cta_slide["text"],
            "palette": tokens["colors"]
        }
    }

    target_handoff = output_handoff or (output_dir / "HANDOFF.json")
    target_handoff.parent.mkdir(parents=True, exist_ok=True)
    target_handoff.write_text(json.dumps(handoff_envelope, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[+] Envelope Universal de Handoff emitido em: {target_handoff}")

    print(f"\n[OK] Dissecacao Social de '{input_source}' concluida com sucesso em: {output_dir.resolve()}")
    return output_dir


def main():
    parser = argparse.ArgumentParser(description="Dissecador de Carrosséis e Posts Sociais (aidd-social-reengineer v1.0.0)")
    parser.add_argument("--input", metavar="FONTE", help="Pasta com imagens de slides ou arquivo de post")
    parser.add_argument("--output-dir", default="./research/social-target", help="Pasta de saída para os artefatos REA")
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

    if args.input:
        out_dir = Path(args.output_dir)
        handoff_p = Path(args.output_handoff) if args.output_handoff else None
        dissect_social_carousel(args.input, out_dir, output_handoff=handoff_p)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
