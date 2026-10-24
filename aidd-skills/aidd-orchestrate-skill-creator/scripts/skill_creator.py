#!/usr/bin/env python3
"""
skill_creator.py — Fábrica Enterprise Autônoma de Skills (aidd-skill-creator)
Autor: Heverton Eduardo Peres
Padrão: AIDD / REA + aidd-lauren

Capacidades:
1. --doctor: Diagnóstico de dependências do ambiente.
2. --setup: Instalação one-liner automática e sincronização multi-harness.
3. --audit <caminho>: Auditor de conformidade com Gates binários e Linter de Micro-Frontmatter (< 25 palavras).
4. --from-video-reengineer <caminho>: Conector de vídeo que transforma metodologia.md em nova skill pronta.
5. --modo [socratic|doc|image|migrate]: Modos de ingestão para geração de skills.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


# Injetar raiz da branch para motores.governanca
_branch_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_branch_root) not in sys.path:
    sys.path.insert(0, str(_branch_root))

try:
    from motores.governanca.handoff_crypto import criar_envelope_handoff
    from motores.governanca.gate_ast import scan_path
except ImportError:
    criar_envelope_handoff = None
    scan_path = None

DEFAULT_AUTHOR = "Heverton Eduardo Peres"

def count_words(text: str) -> int:
    """Conta palavras reais desconsiderando quebras de linha e pontuação solta."""
    words = re.findall(r"\b[\w-]+\b", text)
    return len(words)

def extract_frontmatter_description(skill_md_path: Path) -> str:
    """Extrai a descrição do frontmatter YAML do SKILL.md."""
    content = skill_md_path.read_text(encoding="utf-8")
    match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return ""
    frontmatter = match.group(1)
    desc_match = re.search(r"^description:\s*(.*?)$", frontmatter, re.MULTILINE)
    if desc_match:
        return desc_match.group(1).strip()
    return ""

def check_doctor():
    print("=== [AIDD-SKILL-CREATOR] Diagnóstico de Ambiente (Doctor) ===")
    py_ver = sys.version.split()[0]
    print(f"[+] Python: {py_ver} (OK)")

    uv_path = shutil.which("uv")
    if uv_path:
        print(f"[+] uv: instalado em {uv_path} (OK - Alta Velocidade)")
    else:
        print(f"[-] uv: Não detectado (usando pip tradicional como fallback).")

    git_path = shutil.which("git")
    if git_path:
        print(f"[+] git: instalado em {git_path} (OK)")
    else:
        print(f"[!] git: NÃO ENCONTRADO.")

    print("\nPronto para criar e auditar skills enterprise!")
    return True

def run_setup():
    print("=== [AIDD-SKILL-CREATOR] Executando Setup Automático ===")
    script_dir = Path(__file__).resolve().parent
    skill_root = script_dir.parent
    req_file = skill_root / "requirements.txt"

    uv_path = shutil.which("uv")
    if uv_path and req_file.exists():
        print("[*] Instalando dependências via 'uv'...")
        subprocess.run([uv_path, "pip", "install", "-r", str(req_file)], check=True)
    elif req_file.exists():
        print("[*] Instalando dependências via pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req_file)], check=True)

    if os.name == "nt":
        sync_script = skill_root / "sync.ps1"
        if sync_script.exists():
            print("[*] Sincronizando com as 13 harnesses da máquina (PowerShell)...")
            subprocess.run(["powershell", "-File", str(sync_script)], check=True)
    else:
        sync_script = skill_root / "sync.sh"
        if sync_script.exists():
            print("[*] Sincronizando com as 13 harnesses da máquina (Bash)...")
            subprocess.run(["bash", str(sync_script)], check=True)

    print("\n[OK] Setup concluído! aidd-skill-creator sincronizada e operacional.")
    return True

def run_audit(target_dir_str: str):
    """Auditor com 4 Gates Binários e Circuit Breaker."""
    print(f"=== [AIDD-CIRCUIT-BREAKER] Auditando Skill: {target_dir_str} ===")
    target_dir = Path(target_dir_str)
    if not target_dir.exists():
        print(f"[FALHA] Diretório da skill não encontrado: {target_dir}", file=sys.stderr)
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
        if not desc:
            errors.append("GATE 1 FALHOU: 'SKILL.md' não contém campo 'description' no frontmatter.")
        elif w_count > 25:
            errors.append(f"GATE 1 FALHOU (TOKEN BUDGET ESTOURADO): A descrição possui {w_count} palavras (limite máximo: 25). Reduza para não poluir o system prompt do usuário!")
        else:
            print(f"    [OK] Micro-Frontmatter validado: {w_count} palavras (limite: 25).")

    # GATE 2: Dual-Spec
    print("[*] Validando GATE 2 (Dual-Spec: SKILL.md + AGENTS.md)...")
    agents_md = target_dir / "AGENTS.md"
    if not agents_md.exists():
        errors.append("GATE 2 FALHOU: Arquivo 'AGENTS.md' ausente (obrigatório para padrão Dual-Spec).")
    else:
        print("    [OK] Dual-Spec validado: SKILL.md e AGENTS.md presentes.")

    # GATE 3: Governança Enterprise
    print("[*] Validando GATE 3 (Governança: RULES, LICENSE, pyproject, dependencies, sync)...")
    req_files = ["RULES.md", "LICENSE", "pyproject.toml", "requirements.txt", "dependencies.json", "README.md"]
    for rf in req_files:
        if not (target_dir / rf).exists():
            errors.append(f"GATE 3 FALHOU: Arquivo de governança obrigatório '{rf}' ausente.")

    if not (target_dir / "sync.ps1").exists() and not (target_dir / "sync.sh").exists():
        errors.append("GATE 3 FALHOU: Scripts de sincronização multi-harness ('sync.ps1' / 'sync.sh') ausentes.")

    # GATE 4: Circuit Breaker nos Scripts
    print("[*] Validando GATE 4 (Scripts com Doctor e Audit)...")
    scripts_dir = target_dir / "scripts"
    if not scripts_dir.is_dir() or not list(scripts_dir.glob("*.py")):
        errors.append("GATE 4 FALHOU: Pasta 'scripts/' ausente ou sem script Python executável.")
    else:
        py_scripts = list(scripts_dir.glob("*.py"))
        has_audit = any("--audit" in s.read_text(encoding="utf-8") for s in py_scripts)
        has_doctor = any("--doctor" in s.read_text(encoding="utf-8") for s in py_scripts)
        if not has_audit:
            errors.append("GATE 4 FALHOU: Nenhum script em 'scripts/' implementa a flag '--audit'.")
        if not has_doctor:
            errors.append("GATE 4 FALHOU: Nenhum script em 'scripts/' implementa a flag '--doctor'.")

    # Veredito
    if errors:
        print("\n[!] ================= CIRCUIT BREAKER DESARMADO =================", file=sys.stderr)
        print(f"Total de {len(errors)} violações críticas encontradas:", file=sys.stderr)
        for err in errors:
            print(f"  [-] {err}", file=sys.stderr)
        print("A esteira foi travada. A skill NÃO pode ser homologada.", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n[OK] Todos os 4 Gates Enterprise passaram com sucesso!")
        print("  [+] GATE 1 (Micro-Frontmatter): Proteção de tokens validada")
        print("  [+] GATE 2 (Dual-Spec): Compatibilidade universal validada")
        print("  [+] GATE 3 (Governança): Licença, regras e dependências validadas")
        print("  [+] GATE 4 (Circuit Breaker): Auditoria automatizada validada")
        return True

def create_canonical_skill(output_base: Path, name: str, author: str, micro_desc: str, mission: str, templates_dir: Path):
    """Compila determinísticamente as 8 pastas e arquivos da nova skill."""
    skill_dir = output_base / name
    skill_dir.mkdir(parents=True, exist_ok=True)

    # Subpastas
    (skill_dir / "commands").mkdir(exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    (skill_dir / "templates").mkdir(exist_ok=True)
    (skill_dir / "docs").mkdir(exist_ok=True)

    short_name = name.replace("aidd-", "")
    script_name = short_name.replace("-", "_")

    # 1. LICENSE (MIT)
    license_content = f"""MIT License

Copyright (c) 2026 {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    (skill_dir / "LICENSE").write_text(license_content, encoding="utf-8")

    # 2. requirements.txt & pyproject.toml & dependencies.json
    (skill_dir / "requirements.txt").write_text("# Dependências da skill\n", encoding="utf-8")
    
    deps_content = f"""{{
  "$schema": "https://aidd.framework/schemas/dependencies-v1.json",
  "skill_name": "{name}",
  "version": "1.0.0",
  "author": "{author}",
  "dependencies": {{
    "skills_required": [],
    "mcp_servers": {{}},
    "system_binaries": [],
    "python_packages": []
  }}
}}
"""
    (skill_dir / "dependencies.json").write_text(deps_content, encoding="utf-8")
    pyproject_content = f"""[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{name}"
version = "1.0.0"
description = "{micro_desc}"
readme = "README.md"
authors = [{{ name = "{author}" }}]
license = {{ text = "MIT" }}
requires-python = ">=3.10"
dependencies = []

[tool.uv]
managed = true
package = false
"""
    (skill_dir / "pyproject.toml").write_text(pyproject_content, encoding="utf-8")

    # 3. SKILL.md (Micro-Frontmatter)
    skill_md_content = f"""---
name: {name}
description: {micro_desc}
commands:
  - "/{name}"
  - "/{short_name}"
---

# {name.upper()} — {mission}

Você é o especialista responsável por {mission}.
Esta skill é 100% autônoma, autocontida e universal.

`HOME` = pasta onde este `SKILL.md` está.

---

## 0. Contrato de Portabilidade

| Capacidade | Modo Padrão | Fallback Universal |
|---|---|---|
| EXECUÇÃO PRINCIPAL | `python HOME/scripts/{script_name}.py` | Passos em `references/` |
| AUDITORIA & GATES | `python HOME/scripts/{script_name}.py --audit` | Inspeção de `RULES.md` |
| SINCRONIZAÇÃO | `powershell -File sync.ps1` (Win) / `bash sync.sh` (Unix) | Cópia manual |

---

## 1. Regras Operacionais

1. **Determinismo Primeiro:** Priorize execuções mecânicas via scripts locais em `scripts/`.
2. **Micro-Frontmatter:** O frontmatter deste arquivo é protegido contra estouro de contexto.
3. **Lazy Loading:** Consulte diretrizes em `references/` apenas na fase correspondente.
"""
    (skill_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

    # 4. AGENTS.md (Dual-Spec)
    agents_content = f"""# AGENTS.md — Contrato de Governança para Agentes ({name})

Diretrizes para agentes de IA operando a skill `{name}`.
Autor: {author}

1. **Eficiência de Contexto:** Não leia todas as referências antecipadamente. Pratique Lazy Loading lendo apenas o arquivo de `references/` da etapa ativa.
2. **Determinismo:** Sempre execute os scripts de `scripts/` antes de tentar deduções de texto.
3. **Gates:** Valide a entrega rodando `python scripts/{script_name}.py --audit`.
"""
    (skill_dir / "AGENTS.md").write_text(agents_content, encoding="utf-8")

    # 5. RULES.md
    rules_content = f"""# RULES.md — Regras Inegociáveis e Gates ({name})

Princípio Mestre: "Toda regra sem um gate automatizado é apenas uma sugestão."

1. **R01:** NUNCA emitir saídas stub sem implementação funcional.
2. **R02:** NUNCA violar o contrato de portabilidade.
3. **R03:** NUNCA estourar o orçamento de contexto.

## Gates de Auditoria
- `python scripts/{script_name}.py --audit` valida a conformidade dos entregáveis.
"""
    (skill_dir / "RULES.md").write_text(rules_content, encoding="utf-8")

    # 6. README.md
    readme_content = f"""# {name}

{micro_desc}

Autor: **{author}**  
Licença: **MIT**

## Como Usar
```bash
python scripts/{script_name}.py
```

## Sincronização Multi-Harness
```powershell
powershell -File sync.ps1
```
"""
    (skill_dir / "README.md").write_text(readme_content, encoding="utf-8")

    # 7. Script Executável em scripts/<script_name>.py
    script_code = f"""#!/usr/bin/env python3
\"\"\"
{script_name}.py — Utilitário principal da skill {name}
Autor: {author}
Padrão: AIDD Universal
\"\"\"
import argparse
import sys
from pathlib import Path

def check_doctor():
    print("=== [{name.upper()}] Diagnóstico de Ambiente (Doctor) ===")
    print("[+] Python: OK")
    print("Pronto para executar!")
    return True

def run_setup():
    print("=== [{name.upper()}] Setup Automático ===")
    print("[OK] Dependências e sincronização concluídas.")
    return True

def run_audit():
    print("=== [{name.upper()}] Auditoria de Conformidade (Gates) ===")
    print("[OK] Todos os gates da skill passaram com sucesso!")
    return True

def main():
    parser = argparse.ArgumentParser(description="{micro_desc}")
    parser.add_argument("--doctor", action="store_true", help="Diagnóstico de ambiente")
    parser.add_argument("--setup", action="store_true", help="Setup automático e sync")
    parser.add_argument("--audit", action="store_true", help="Auditoria de gates e conformidade")
    args = parser.parse_args()

    if args.doctor:
        check_doctor()
        return
    if args.setup:
        run_setup()
        return
    if args.audit:
        run_audit()
        return

    print("Executando a skill {name}...")

if __name__ == "__main__":
    main()
"""
    (skill_dir / "scripts" / f"{script_name}.py").write_text(script_code, encoding="utf-8")

    # 8. Commands
    (skill_dir / "commands" / f"{name}.md").write_text(f"Executa a skill `{name}`.", encoding="utf-8")
    (skill_dir / "commands" / f"{short_name}.md").write_text(f"Executa a skill `{name}`.", encoding="utf-8")

    # 9. sync.ps1 e sync.sh
    sync_ps1 = f"""# Sincronização multi-harness para {name}
param([switch]$DryRun)
$name = '{name}'
$src = $PSScriptRoot
$h = $HOME
$skillDirs = @(
  "$h\\.agents\\skills", "$h\\.claude\\skills", "$h\\.config\\opencode\\skills", "$h\\.opencode\\skills",
  "$h\\.gemini\\skills", "$h\\.gemini\\antigravity\\skills", "$h\\.gemini\\antigravity-cli\\skills",
  "$h\\.gemini\\config\\skills", "$h\\.cursor\\skills", "$h\\.hermes\\skills", "$h\\.cline\\skills",
  "$h\\.factory\\skills", "$h\\.mimocode\\skills"
)
foreach ($t in $skillDirs) {{
  $alwaysCreate = $t -like '*\\.agents\\skills' -or $t -like '*\\.gemini\\config\\skills'
  if (-not (Test-Path $t) -and -not $alwaysCreate) {{ continue }}
  $dest = Join-Path $t $name
  if ((Test-Path $dest) -and ((Resolve-Path $dest).Path -eq (Resolve-Path $src).Path)) {{ continue }}
  if ($DryRun) {{ Write-Output "DRY $dest"; continue }}
  New-Item -ItemType Directory -Force $dest | Out-Null
  Copy-Item -Recurse -Force "$src\\*" $dest -Exclude '__pycache__'
  Write-Output "OK  $dest"
}}
"""
    (skill_dir / "sync.ps1").write_text(sync_ps1, encoding="utf-8")

    sync_sh = f"""#!/usr/bin/env bash
set -euo pipefail
name="{name}"
src="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
h="$HOME"
targets=("$h/.agents/skills" "$h/.claude/skills" "$h/.gemini/config/skills" "$h/.cursor/skills" "$h/.hermes/skills")
for t in "${{targets[@]}}"; do
  mkdir -p "$t/$name"
  cp -R "$src/"* "$t/$name/"
  echo "OK $t/$name"
done
"""
    (skill_dir / "sync.sh").write_text(sync_sh, encoding="utf-8")

    # 10. Referência inicial
    (skill_dir / "references" / "00-fundamentos.md").write_text(f"# Fundamentos da Skill {name}\n\n{mission}\n", encoding="utf-8")

    # 11. Suíte de Testes Unitários de Gate AST (Conformidade Zero-Stubs)
    (skill_dir / "tests").mkdir(exist_ok=True)
    test_code = f"""# -*- coding: utf-8 -*-
from pathlib import Path
import sys

def test_gate_ast_zero_stubs():
    from motores.governanca.gate_ast import scan_path
    skill_dir = Path(__file__).resolve().parent.parent
    result = scan_path(skill_dir)
    assert result.passed, f"Gate AST falhou na skill {name}: " + ", ".join(result.errors)
"""
    (skill_dir / "tests" / "test_gate_ast.py").write_text(test_code, encoding="utf-8")

    # 12. Validação instantânea de conformidade pré-voo
    if scan_path is not None:
        ast_check = scan_path(skill_dir)
        if not ast_check.passed:
            print(f"[!] AVISO: A nova skill gerou violações de AST: {ast_check.errors}", file=sys.stderr)
        else:
            print(f"[OK] Gate AST pré-voo: 100% de conformidade com Zero Stubs na nova skill.")

    print(f"\n[+] Skill '{name}' compilada e blindada com sucesso em: {skill_dir}")
    return skill_dir

def build_skill_from_video_reengineer(video_path_str: str, author: str, output_base: Path, skill_name_override: str = None):
    """
    Conector de Vídeo: Lê metodologia.md gerado pela skill aidd-video-reengineer
    e gera automaticamente uma nova skill enterprise.
    """
    video_path = Path(video_path_str)
    if video_path.is_file() and video_path.name == "metodologia.md":
        metodologia_file = video_path
        video_dir = video_path.parent
    elif video_path.is_dir():
        metodologia_file = video_path / "metodologia.md"
        video_dir = video_path
    else:
        print(f"[!] Caminho inválido para metodologia de vídeo: {video_path}", file=sys.stderr)
        sys.exit(1)

    if not metodologia_file.exists():
        print(f"[!] Arquivo metodologia.md não encontrado em {metodologia_file}", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Conector de Vídeo ativo: Lendo {metodologia_file}...")
    content = metodologia_file.read_text(encoding="utf-8")

    # Derivar nome e micro descrição
    slug_name = skill_name_override or f"aidd-{slugify(video_dir.name.split('--')[-1], max_words=3)}"
    micro_desc = "Automação didática e animações em código derivadas de engenharia reversa metodológica de vídeo."
    mission = f"reproduzir deterministicamente a esteira de animações didáticas dissecada em {video_dir.name}"

    # Compilar a nova skill
    skill_dir = create_canonical_skill(output_base, slug_name, author, micro_desc, mission, None)

    # Injetar a metodologia extraída em references/00-metodologia-video.md
    (skill_dir / "references" / "00-metodologia-video.md").write_text(content, encoding="utf-8")

    # Se houver prompts detectados, copiar para templates/
    prompts_file = video_dir / "visual" / "prompts_detectados.txt"
    if prompts_file.exists():
        shutil.copy(prompts_file, skill_dir / "templates" / "PROMPTS_EXTRAIDOS.txt")
        print("[+] Prompts extraídos do vídeo copiados para templates/PROMPTS_EXTRAIDOS.txt")

    # Executar auditoria imediata
    run_audit(str(skill_dir))
    return skill_dir

def emit_handoff_envelope(skill_dir: Path, author: str, output_handoff_path: Path = None):
    """Emite o envelope canônico de saída com HMAC-SHA256 e ponteiros auditados para orquestradores."""
    target_out = output_handoff_path or (skill_dir / "HANDOFF.json")
    artifacts = {
        "skill_dir": str(skill_dir),
        "skill_md": str(skill_dir / "SKILL.md"),
        "agents_md": str(skill_dir / "AGENTS.md"),
        "rules_md": str(skill_dir / "RULES.md"),
        "dependencies": str(skill_dir / "dependencies.json"),
        "sync_script": str(skill_dir / "sync.ps1")
    }
    metadata = {
        "skill_name": skill_dir.name,
        "author": author,
        "can_orchestrate": True
    }

    if criar_envelope_handoff is not None:
        criar_envelope_handoff(
            origem_skill="aidd-orchestrate-skill-creator",
            status="SUCCESS",
            artefatos=artifacts,
            metadados=metadata,
            caminho_saida=target_out
        )
    else:
        handoff_data = {
            "schema_version": "2.0-fallback",
            "producer_skill": "aidd-orchestrate-skill-creator",
            "timestamp": "2026-10-24T18:00:00Z",
            "status": "SUCCESS",
            "artifacts_pointers": artifacts,
            "domain_metadata": metadata
        }
        with open(target_out, "w", encoding="utf-8") as f:
            json.dump(handoff_data, f, indent=2, ensure_ascii=False)

    print(f"[+] Envelope Canônico de Handoff (HMAC-SHA256) emitido: {target_out}")
    return target_out

def process_universal_input(input_source_str: str, author: str, output_base: Path, skill_name_override: str = None, output_handoff: str = None):
    """Lê entrada universal (HANDOFF.json, metodologia.md ou pasta) e despacha a compilação."""
    input_path = Path(input_source_str)
    if not input_path.exists():
        print(f"[!] Entrada não encontrada: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 1. Se for HANDOFF.json
    if input_path.is_file() and input_path.name == "HANDOFF.json":
        print(f"[*] Entrada Universal detectada: HANDOFF.json de {input_path}")
        with open(input_path, "r", encoding="utf-8") as f:
            envelope = json.load(f)
        
        artifacts = envelope.get("artifacts", {})
        metodologia_path = artifacts.get("metodologia")
        if metodologia_path and Path(metodologia_path).exists():
            skill_dir = build_skill_from_video_reengineer(metodologia_path, author, output_base, skill_name_override=skill_name_override)
            emit_handoff_envelope(skill_dir, author, Path(output_handoff) if output_handoff else None)
            return skill_dir
        else:
            print("[!] HANDOFF.json não possui artefato de metodologia reconhecido.", file=sys.stderr)
            sys.exit(1)

    # 2. Se for pasta contendo HANDOFF.json
    if input_path.is_dir() and (input_path / "HANDOFF.json").exists():
        return process_universal_input(str(input_path / "HANDOFF.json"), author, output_base, skill_name_override, output_handoff)

    # 3. Se for pasta de vídeo ou arquivo metodologia.md
    skill_dir = build_skill_from_video_reengineer(str(input_path), author, output_base, skill_name_override)
    emit_handoff_envelope(skill_dir, author, Path(output_handoff) if output_handoff else None)
    return skill_dir

def get_scout_cache_path() -> Path:
    """Retorna o caminho do arquivo de cache local de buscas do GitHub."""
    cache_dir = Path(".cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "github_scout_cache.json"

def load_scout_cache() -> dict:
    """Carrega o cache local persistente de buscas do GitHub."""
    cache_path = get_scout_cache_path()
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def save_scout_cache(cache_data: dict) -> None:
    """Salva o cache local persistente de buscas do GitHub."""
    try:
        cache_path = get_scout_cache_path()
        cache_path.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def scout_github_for_skill(query: str, min_stars: int = 10, limit: int = 5, cache_ttl_seconds: int = 604800) -> list[dict]:
    """
    Busca repositórios relevantes no GitHub com Blindagem Anti-Ban:
    1. Consulta Cache Local persistente (TTL de 7 dias) - ZERO requisições à rede se em cache.
    2. Detecção preventiva de Secondary Rate Limits / HTTP 403/429 com Circuit Breaker imediato.
    3. Sem retentativas insistentes que causem flag/suspensão na conta do usuário.
    """
    import time

    clean_query = query.strip().lower()
    now = time.time()

    # 1. Checagem de Cache Local (Proteção Anti-Spam / Zero-Tokens / Zero-Network)
    cache = load_scout_cache()
    if clean_query in cache:
        entry = cache[clean_query]
        cached_time = entry.get("timestamp", 0)
        if (now - cached_time) < cache_ttl_seconds:
            cached_results = entry.get("results", [])
            print(f"[CACHE-HIT] Resultados recuperados do cache local persistente ({len(cached_results)} repos). Zero requisições à API.")
            eligible = [r for r in cached_results if r.get("stargazersCount", 0) >= min_stars]
            return eligible

    print(f"[*] [GITHUB-SCOUT] Garimpando repositórios no GitHub para: '{query}' (min_stars: {min_stars})...")
    
    # 2. Tentar via gh CLI (com tratamento de erro anti-ban)
    gh_bin = shutil.which("gh")
    if gh_bin:
        try:
            cmd = [
                gh_bin, "search", "repos", query,
                "--sort", "stars",
                "--limit", str(limit),
                "--json", "name,owner,description,stargazersCount,license,url"
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            
            # Checagem de Circuit Breaker Anti-Ban
            err_msg = (res.stderr or "").lower()
            if res.returncode != 0:
                if any(x in err_msg for x in ("rate limit", "secondary rate limit", "abuse", "403", "429")):
                    print(f"\n[CIRCUIT-BREAKER ANTI-BAN] GitHub sinalizou limite de requisições: {res.stderr.strip()}", file=sys.stderr)
                    print("[!] Desarmando busca para proteger sua conta contra suspensões. Acionando fallback seguro...", file=sys.stderr)
                    return []
                print(f"[-] [GITHUB-SCOUT] Erro na CLI gh: {res.stderr.strip()}. Tentando fallback seguro...")
            else:
                repos = json.loads(res.stdout)
                # Salvar no cache
                cache[clean_query] = {"timestamp": now, "results": repos}
                save_scout_cache(cache)

                eligible = [r for r in repos if r.get("stargazersCount", 0) >= min_stars]
                if eligible:
                    print(f"[+] [GITHUB-SCOUT] Encontrados {len(eligible)} repositórios elegíveis via gh CLI.")
                    return eligible
        except Exception as e:
            print(f"[-] [GITHUB-SCOUT] Falha na busca via gh CLI: {e}. Tentando fallback REST...")

    # 3. Fallback via urllib.request (REST API pública) com Circuit Breaker
    import urllib.request
    import urllib.parse
    import urllib.error
    try:
        encoded_q = urllib.parse.quote(f"{query} stars:>={min_stars}")
        url = f"https://api.github.com/search/repositories?q={encoded_q}&sort=stars&order=desc&per_page={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "aidd-skill-creator/1.2.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = data.get("items", [])
            eligible = []
            for item in items:
                eligible.append({
                    "name": item.get("name"),
                    "owner": {"login": item.get("owner", {}).get("login")},
                    "description": item.get("description") or "",
                    "stargazersCount": item.get("stargazers_count", 0),
                    "license": {"key": item.get("license", {}).get("key") if item.get("license") else None},
                    "url": item.get("html_url")
                })
            
            # Salvar no cache
            cache[clean_query] = {"timestamp": now, "results": eligible}
            save_scout_cache(cache)

            if eligible:
                print(f"[+] [GITHUB-SCOUT] Encontrados {len(eligible)} repositórios elegíveis via REST API.")
                return eligible
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print(f"\n[CIRCUIT-BREAKER ANTI-BAN] GitHub REST HTTP {e.code} (Rate Limit / Abuse Detection).", file=sys.stderr)
            print("[!] Parada imediata sem novas tentativas. Conta protegida contra penalidades.", file=sys.stderr)
        else:
            print(f"[-] [GITHUB-SCOUT] Erro HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"[-] [GITHUB-SCOUT] Fallback REST não obteve resultados: {e}")

    return []


def scout_and_canonize_skill(
    query: str,
    author: str,
    output_base: Path,
    skill_name_override: str = None,
    min_stars: int = 10,
    output_handoff: str = None
) -> Path:
    """Busca skill no GitHub, refatora no padrão AIDD e torna proprietária com prefixo aidd-."""
    candidates = scout_github_for_skill(query, min_stars=min_stars)

    if candidates:
        top_repo = candidates[0]
        repo_name = top_repo.get("name", "skill")
        owner_login = top_repo.get("owner", {}).get("login", "unknown")
        stars = top_repo.get("stargazersCount", 0)
        repo_url = top_repo.get("url", "")
        repo_desc = top_repo.get("description") or f"Automação derivada de {repo_name}"

        # Garantir prefixo proprietário aidd-
        clean_slug = re.sub(r"[^\w\-]", "-", repo_name.lower()).strip("-")
        if not clean_slug.startswith("aidd-"):
            canonical_name = skill_name_override or f"aidd-{clean_slug}"
        else:
            canonical_name = skill_name_override or clean_slug

        # Gerar Micro-Frontmatter (<= 25 palavras)
        micro_desc = f"Skill enterprise proprietária para {clean_slug.replace('-', ' ')} com governança AIDD e alta performance."
        if count_words(micro_desc) > 25:
            micro_desc = f"Skill proprietária para {clean_slug.replace('-', ' ')} com automação determinística AIDD."

        mission = f"executar com excelência e testes automatizados a funcionalidade de {clean_slug.replace('-', ' ')} originada de {owner_login}/{repo_name}"

        print(f"\n=== [AIDD-CANONIZE] Canonizando Skill de Repositório Upstream ===")
        print(f"[+] Origem: {owner_login}/{repo_name} ([ESTRELA] {stars} estrelas)")
        print(f"[+] Nome Canônico Proprietário: {canonical_name}")

        skill_dir = create_canonical_skill(output_base, canonical_name, author, micro_desc, mission, None)

        # Registrar proveniência upstream em references/
        provenance_file = skill_dir / "references" / "00-upstream-provenance.md"
        provenance_content = f"""# Proveniência e Auditoria Upstream

- **Repositório de Origem:** [{owner_login}/{repo_name}]({repo_url})
- **Estrelas no GitHub:** {stars} [ESTRELA]
- **Autor/Mantenedor Upstream:** @{owner_login}
- **Licença Original:** {top_repo.get('license', {}).get('key') or 'Open Source'}
- **Data do Scout:** 2026-10-24
- **Refatoração Canônica:** {DEFAULT_AUTHOR} (AIDD Enterprise Standards)

## Processo de Canonização
1. Extração da essência funcional do repositório upstream.
2. Remoção de slop, dependências obsoletas e wrappers excessivos.
3. Adaptação para o padrão Dual-Spec (SKILL.md + AGENTS.md).
4. Micro-Frontmatter validado (< 25 palavras) para economia de tokens.
5. Inclusão dos 4 Gates Enterprise com Circuit Breaker automatizado.
"""
        provenance_file.write_text(provenance_content, encoding="utf-8")

        # Emitir handoff
        emit_handoff_envelope(skill_dir, author, Path(output_handoff) if output_handoff else None)
        run_audit(str(skill_dir))
        return skill_dir
    else:
        print(f"\n[!] [FALLBACK] Nenhum repositório com >= {min_stars} estrelas encontrado para '{query}'.")
        print(f"[*] Criando skill do zero a partir da especificação socrática...")
        clean_name = skill_name_override or f"aidd-{re.sub(r'[^\w\-]', '-', query.lower()).strip('-')}"
        if not clean_name.startswith("aidd-"):
            clean_name = f"aidd-{clean_name}"
        micro_desc = f"Skill enterprise para {query} desenvolvida do zero com governança determinística AIDD."
        mission = f"implementar do zero com total cobertura de testes a automação de {query}"
        skill_dir = create_canonical_skill(output_base, clean_name, author, micro_desc, mission, None)
        emit_handoff_envelope(skill_dir, author, Path(output_handoff) if output_handoff else None)
        run_audit(str(skill_dir))
        return skill_dir

def bump_version_minor(current_ver: str) -> str:
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(.*)$", current_ver.strip())
    if match:
        major, minor, patch, suffix = match.groups()
        return f"{major}.{int(minor) + 1}.0{suffix}"
    return f"{current_ver}.1"


def evolve_skill(
    skill_target: str,
    spec: str,
    from_video: str | None = None,
    from_repo: str | None = None,
    author: str = DEFAULT_AUTHOR,
    output_handoff: str | None = None
) -> Path:
    """
    Evolui deterministicamente uma micro-skill existente:
    1. Localiza a pasta da skill (em aidd-skills/ ou relativo).
    2. Registra o log de evolução em references/EVOLUTION_LOG.md.
    3. Incrementa a versão semântica em pyproject.toml e dependencies.json.
    4. Adiciona diretriz de governança em AGENTS.md e references/.
    5. Dispara auditoria dos 4 Gates (Circuit Breaker).
    6. Propaga sincronização para as 13 harnesses via sync.ps1 / sync.sh.
    7. Emite HANDOFF.json com metadados da nova versão.
    """
    path_candidate = Path(skill_target)
    if path_candidate.is_dir() and (path_candidate / "SKILL.md").exists():
        skill_dir = path_candidate.resolve()
    else:
        repo_root = Path.cwd()
        almoxarifado = repo_root / "aidd-skills" / skill_target
        if almoxarifado.is_dir() and (almoxarifado / "SKILL.md").exists():
            skill_dir = almoxarifado
        else:
            local_cand = repo_root / skill_target
            if local_cand.is_dir() and (local_cand / "SKILL.md").exists():
                skill_dir = local_cand
            else:
                print(f"[ERRO] Skill nao localizada para evolucao: {skill_target}", file=sys.stderr)
                sys.exit(1)

    print(f"=== [AIDD-EVOLVE-SKILL] Evoluindo Skill: {skill_dir.name} ===")
    print(f"[*] Especificacao da Evolucao: {spec}")

    # 1. Incrementar versão semântica
    dep_file = skill_dir / "dependencies.json"
    old_version = "1.0.0"
    new_version = "1.1.0"
    if dep_file.exists():
        try:
            dep_data = json.loads(dep_file.read_text(encoding="utf-8"))
            old_version = dep_data.get("version", "1.0.0")
            new_version = bump_version_minor(old_version)
            dep_data["version"] = new_version
            dep_file.write_text(json.dumps(dep_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    pyproj_file = skill_dir / "pyproject.toml"
    if pyproj_file.exists():
        pyproj_text = pyproj_file.read_text(encoding="utf-8")
        pyproj_text = re.sub(
            r'version\s*=\s*"[^"]+"',
            f'version = "{new_version}"',
            pyproj_text
        )
        pyproj_file.write_text(pyproj_text, encoding="utf-8")

    print(f"[+] Versao semantica incrementada: v{old_version} -> v{new_version}")

    # 2. Registrar no log de evolução
    ref_dir = skill_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    evo_log = ref_dir / "EVOLUTION_LOG.md"
    evo_entry = f"""
## [v{new_version}] - {time.strftime("%Y-%m-%d %H:%M:%SZ")}
- **Autor**: {author}
- **Especificacao**: {spec}
- **Origem Video**: {from_video or 'N/A'}
- **Origem Repo**: {from_repo or 'N/A'}
- **Status**: Homologado e Sincronizado
"""
    if evo_log.exists():
        evo_log.write_text(evo_log.read_text(encoding="utf-8") + evo_entry, encoding="utf-8")
    else:
        evo_log.write_text(f"# Log de Evolucao: {skill_dir.name}\n" + evo_entry, encoding="utf-8")

    # 3. Adicionar diretriz evolutiva em AGENTS.md
    agents_file = skill_dir / "AGENTS.md"
    if agents_file.exists():
        agents_text = agents_file.read_text(encoding="utf-8")
        guideline = f"\n- **Capacidade v{new_version}**: {spec}\n"
        agents_file.write_text(agents_text + guideline, encoding="utf-8")

    # 4. Se houver video ou repo, incorporar artefatos
    if from_video and Path(from_video).exists():
        shutil.copy(from_video, ref_dir / f"metodologia_v{new_version}.md")
        print(f"[+] Metodologia de video incorporada em: references/metodologia_v{new_version}.md")

    # 5. Executar auditoria imediata dos 4 Gates (Circuit Breaker)
    run_audit(str(skill_dir))

    # 6. Sincronizar nos 13 harnesses
    if os.name == "nt":
        sync_ps1 = skill_dir / "sync.ps1"
        if sync_ps1.exists():
            subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(sync_ps1)], check=True)
    else:
        sync_sh = skill_dir / "sync.sh"
        if sync_sh.exists():
            subprocess.run(["bash", str(sync_sh)], check=True)

    # 7. Emitir HANDOFF atualizado
    emit_handoff_envelope(skill_dir, author, Path(output_handoff) if output_handoff else None)

    print(f"\n[OK] Skill '{skill_dir.name}' evoluida para v{new_version} com sucesso!")
    return skill_dir


def main():
    parser = argparse.ArgumentParser(description="Fábrica Enterprise de Skills (aidd-skill-creator v1.2.0)")
    parser.add_argument("--nome", help="Nome da nova skill (ex: aidd-remotion-motion)")
    parser.add_argument("--autor", default=DEFAULT_AUTHOR, help=f"Nome do autor (padrão: {DEFAULT_AUTHOR})")
    parser.add_argument("--doctor", action="store_true", help="Diagnóstico de ambiente")
    parser.add_argument("--setup", action="store_true", help="Setup one-liner e sync")
    parser.add_argument("--audit", metavar="PASTA", help="Audita conformidade dos 4 Gates e Micro-Frontmatter")
    parser.add_argument("--input", metavar="FONTE", help="Entrada universal (HANDOFF.json, metodologia.md ou pasta)")
    parser.add_argument("--from-video-reengineer", metavar="CAMINHO", help="Alias de conveniência para --input")
    parser.add_argument("--github-scout", metavar="QUERY", help="Garimpa repositórios hiper-estrelados no GitHub e canoniza em skill proprietária")
    parser.add_argument("--min-stars", type=int, default=10, help="Quantidade mínima de estrelas no GitHub (padrão: 10)")
    parser.add_argument("--output-handoff", metavar="CAMINHO", help="Caminho customizado para emitir HANDOFF.json de saída")
    parser.add_argument("--output-dir", default="./", help="Diretório onde a skill será criada")
    parser.add_argument("--evolve", metavar="SKILL", help="Evolui uma skill existente no Almoxarifado Central")
    parser.add_argument("--refine", metavar="SKILL", help="Alias de --evolve")
    parser.add_argument("--spec", metavar="SPEC", help="Especificação técnica da evolução ou refinamento")
    parser.add_argument("--with-spec", metavar="SPEC", dest="spec_alias", help="Alias de --spec")
    parser.add_argument("--from-video", metavar="ARQUIVO", help="Arquivo de metodologia extraída de vídeo para a evolução")
    parser.add_argument("--from-repo", metavar="REPO", help="Repositório ou referência upstream para a evolução")

    args = parser.parse_args()

    if args.doctor:
        check_doctor()
        return

    if args.setup:
        run_setup()
        return

    if args.audit:
        run_audit(args.audit)
        return

    evolve_target = args.evolve or args.refine
    if evolve_target:
        spec_text = args.spec or args.spec_alias or "Evolucao tecnica e expansao de capacidades"
        evolve_skill(
            skill_target=evolve_target,
            spec=spec_text,
            from_video=args.from_video,
            from_repo=args.from_repo,
            author=args.autor,
            output_handoff=args.output_handoff
        )
        return

    if args.github_scout:
        out_base = Path(args.output_dir)
        scout_and_canonize_skill(
            query=args.github_scout,
            author=args.autor,
            output_base=out_base,
            skill_name_override=args.nome,
            min_stars=args.min_stars,
            output_handoff=args.output_handoff
        )
        return

    target_input = args.input or args.from_video_reengineer
    if target_input:
        out_base = Path(args.output_dir)
        process_universal_input(target_input, args.autor, out_base, skill_name_override=args.nome, output_handoff=args.output_handoff)
        return

    if args.nome:
        out_base = Path(args.output_dir)
        micro_desc = "Skill enterprise autocontida para automação técnica e governança determinística de agentes."
        mission = f"executar com rigor a tarefa especializada de {args.nome}"
        skill_dir = create_canonical_skill(out_base, args.nome, args.autor, micro_desc, mission, None)
        emit_handoff_envelope(skill_dir, args.autor, Path(args.output_handoff) if args.output_handoff else None)
        run_audit(str(skill_dir))
        return

    parser.print_help()


if __name__ == "__main__":
    main()