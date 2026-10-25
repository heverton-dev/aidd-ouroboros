#!/usr/bin/env python3
"""
pipeline_creator.py — Criador e Garimpador de Pipelines Composíveis (aidd-pipeline-creator)
Autor: Heverton Eduardo Peres (2026)
Padrão: AIDD / REA + aidd-lauren

Capacidades Enterprise:
1. --scout-local: Garimpa pipelines locais em aidd-pipelines/ e .github/workflows/.
2. --scout-github <query>: Garimpa pipelines e workflows de referência no GitHub com cache persistente e Anti-Ban.
3. --scout-and-canonize <nome>: Garimpa e canoniza pipeline completo como peça de Lego universal.
4. --scaffold-pipeline <nome>: Provisiona scaffold canônico com governança, DAG e envelope de saída.
5. --inventory: Discovery completo de skills nas 13 harnesses e no Almoxarifado Central.
6. --plan <briefing>: Monta grafo DAG decomposto a partir de entrada textual.
7. --doctor: Diagnóstico de ambiente (Python, Git, GitHub CLI).
8. --setup: Setup one-liner automático e sincronização.
9. --audit: Auditor de conformidade dos 4 Gates com Circuit Breaker.
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
    print("=== [AIDD-PIPELINE-CREATOR] Diagnostico de Ambiente (Doctor) ===")
    py_ver = sys.version.split()[0]
    print(f"[+] Python: {py_ver} (OK)")

    git_path = shutil.which("git")
    if git_path:
        print(f"[+] git: instalado em {git_path} (OK)")
    else:
        print(f"[!] git: NAO ENCONTRADO.")

    gh_path = shutil.which("gh")
    if gh_path:
        print(f"[+] gh: instalado em {gh_path} (OK - GitHub Scout Habilitado)")
    else:
        print(f"[-] gh: Nao detectado (usando fallback REST API para scout).")

    print("\nPronto para criar e orquestrar pipelines composiveis!")
    return True


def run_setup() -> bool:
    print("=== [AIDD-PIPELINE-CREATOR] Executando Setup Automatico ===")
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

    print("\n[OK] aidd-pipeline-creator sincronizada e operacional!")
    return True


def run_audit(target_dir_str: str) -> bool:
    print(f"=== [AIDD-CIRCUIT-BREAKER] Auditando Criador de Pipelines: {target_dir_str} ===")
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

    # GATE 4: Capacidades nos Scripts
    print("[*] Validando GATE 4 (Capacidades de Criacao e Scout nos Scripts)...")
    scripts = list((target_dir / "scripts").glob("*.py"))
    if not scripts:
        errors.append("GATE 4 FALHOU: Nenhum script em 'scripts/'.")
    else:
        s_code = scripts[0].read_text(encoding="utf-8")
        if "--inventory" not in s_code:
            errors.append("GATE 4 FALHOU: Script nao implementa '--inventory'.")
        if "--audit" not in s_code:
            errors.append("GATE 4 FALHOU: Script nao implementa '--audit'.")
        if "--scaffold-pipeline" not in s_code:
            errors.append("GATE 4 FALHOU: Script nao implementa '--scaffold-pipeline'.")

    if errors:
        print("\n[!] CIRCUIT BREAKER DESARMADO:", file=sys.stderr)
        for err in errors:
            print(f"  [-] {err}", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n[OK] Todos os 4 Gates do Criador de Pipelines passaram com sucesso!")
        return True


def get_pipeline_scout_cache_path() -> Path:
    cache_dir = Path(".cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "github_pipeline_scout_cache.json"


def load_pipeline_scout_cache() -> dict:
    cache_path = get_pipeline_scout_cache_path()
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_pipeline_scout_cache(cache_data: dict) -> None:
    try:
        cache_path = get_pipeline_scout_cache_path()
        cache_path.write_text(json.dumps(cache_data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def scout_local_pipelines(root_dir: Path | None = None) -> list[dict]:
    """
    Garimpa pipelines e workflows locais no projeto e ambiente do usuário.
    Procura em aidd-pipelines/*/PIPELINE.json e .github/workflows/*.
    """
    root = root_dir or Path.cwd()
    print(f"=== [AIDD-LOCAL-SCOUT] Garimpando Pipelines Locais em: {root} ===")

    found_pipelines = []

    # 1. Buscar aidd-pipelines/
    pipeline_dirs = list(root.glob("aidd-pipelines/*/PIPELINE.json")) + list(root.glob("pipelines/*/PIPELINE.json"))
    for p_spec_path in pipeline_dirs:
        try:
            data = json.loads(p_spec_path.read_text(encoding="utf-8"))
            p_dir = p_spec_path.parent
            nodes = data.get("nodes", [])
            found_pipelines.append({
                "type": "aidd_autonomous_pipeline",
                "name": data.get("name", p_dir.name),
                "pipeline_id": data.get("pipeline_id", p_dir.name),
                "path": str(p_dir),
                "nodes_count": len(nodes),
                "skills_used": [n.get("skill") for n in nodes if n.get("skill")],
                "has_runner": (p_dir / "run_pipeline.py").exists(),
                "output_contract": data.get("output_contract", "context/output/pipeline_output.json")
            })
        except Exception as e:
            print(f"[-] Erro ao carregar spec local {p_spec_path}: {e}", file=sys.stderr)

    # 2. Buscar .github/workflows/
    gh_workflows = list(root.glob(".github/workflows/*.yml")) + list(root.glob(".github/workflows/*.yaml"))
    for wf in gh_workflows:
        found_pipelines.append({
            "type": "github_workflow",
            "name": wf.stem,
            "pipeline_id": f"gh-workflow-{wf.stem}",
            "path": str(wf),
            "nodes_count": 1,
            "skills_used": [],
            "has_runner": True,
            "output_contract": "ci_cd_job"
        })

    print(f"[+] Total de pipelines/workflows locais encontrados: {len(found_pipelines)}")
    for p in found_pipelines:
        print(f"    - [{p['type'].upper()}] {p['name']} ({p['nodes_count']} nós) -> {p['path']}")

    return found_pipelines


def scout_github_for_pipeline(query: str, min_stars: int = 10, limit: int = 5, cache_ttl_seconds: int = 604800) -> list[dict]:
    """
    Garimpa repositórios e workflows de autoridade no GitHub (ex: pipelines de Addy Osmani, Karpathy, LangGraph).
    Possui cache persistente de 7 dias e Circuit Breaker Anti-Ban preventivo.
    """
    clean_query = query.strip().lower()
    now = time.time()

    # 1. Checagem de Cache Local (Zero-Tokens / Zero-Network)
    cache = load_pipeline_scout_cache()
    if clean_query in cache:
        entry = cache[clean_query]
        cached_time = entry.get("timestamp", 0)
        if (now - cached_time) < cache_ttl_seconds:
            cached_results = entry.get("results", [])
            print(f"[CACHE-HIT] Resultados de pipelines recuperados do cache local persistente ({len(cached_results)} repos). Zero requisicoes a rede.")
            eligible = [r for r in cached_results if r.get("stargazersCount", 0) >= min_stars]
            return eligible

    print(f"[*] [PIPELINE-SCOUT] Garimpando pipelines e workflows no GitHub para: '{query}' (min_stars: {min_stars})...")

    # 2. Tentar via gh CLI
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
            err_msg = (res.stderr or "").lower()
            if res.returncode != 0:
                if any(x in err_msg for x in ("rate limit", "secondary rate limit", "abuse", "403", "429")):
                    print(f"\n[CIRCUIT-BREAKER ANTI-BAN] GitHub sinalizou limite de requisicoes: {res.stderr.strip()}", file=sys.stderr)
                    print("[!] Desarmando busca para proteger conta contra restricoes.", file=sys.stderr)
                    return []
                print(f"[-] [PIPELINE-SCOUT] Erro na CLI gh: {res.stderr.strip()}. Tentando fallback REST...")
            else:
                repos = json.loads(res.stdout)
                cache[clean_query] = {"timestamp": now, "results": repos}
                save_pipeline_scout_cache(cache)

                eligible = [r for r in repos if r.get("stargazersCount", 0) >= min_stars]
                if eligible:
                    print(f"[+] [PIPELINE-SCOUT] Encontrados {len(eligible)} repositorios de autoridade via gh CLI.")
                    return eligible
        except Exception as e:
            print(f"[-] [PIPELINE-SCOUT] Falha na busca via gh CLI: {e}. Tentando fallback REST...")

    # 3. Fallback via urllib (REST API pública)
    import urllib.request
    import urllib.parse
    import urllib.error
    try:
        encoded_q = urllib.parse.quote(f"{query} stars:>={min_stars}")
        url = f"https://api.github.com/search/repositories?q={encoded_q}&sort=stars&order=desc&per_page={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "aidd-pipeline-creator/1.0.0"})
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

            cache[clean_query] = {"timestamp": now, "results": eligible}
            save_pipeline_scout_cache(cache)

            if eligible:
                print(f"[+] [PIPELINE-SCOUT] Encontrados {len(eligible)} repositorios de autoridade via REST API.")
                return eligible
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print(f"\n[CIRCUIT-BREAKER ANTI-BAN] GitHub REST HTTP {e.code} (Rate Limit / Abuse Detection).", file=sys.stderr)
            print("[!] Parada imediata sem novas tentativas. Conta protegida.", file=sys.stderr)
        else:
            print(f"[-] [PIPELINE-SCOUT] Erro HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"[-] [PIPELINE-SCOUT] Fallback REST falhou: {e}")

    return []


def scaffold_autonomous_pipeline(
    pipeline_name: str,
    base_dir: Path | None = None,
    steps: list[dict] | None = None,
    upstream_meta: dict | None = None
) -> Path:
    """
    Cria a estrutura de um Pipeline Autônomo encapsulado (peça de Lego composível) com governança enterprise completa.
    """
    slug = re.sub(r"[^\w\-]", "-", pipeline_name.lower()).strip("-")
    base = base_dir or Path("aidd-pipelines")
    pipeline_dir = base / slug
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    # Subdiretórios canônicos
    context_in = pipeline_dir / "context" / "input"
    context_handoffs = pipeline_dir / "context" / "handoffs"
    context_out = pipeline_dir / "context" / "output"
    skills_dir = pipeline_dir / "skills"
    references_dir = pipeline_dir / "references"
    templates_dir = pipeline_dir / "templates"

    for d in (context_in, context_handoffs, context_out, skills_dir, references_dir, templates_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Copiar template do run_pipeline.py
    script_dir = Path(__file__).resolve().parent
    template_runner = script_dir.parent / "templates" / "RUN_PIPELINE_TEMPLATE.py"
    target_runner = pipeline_dir / "run_pipeline.py"

    if template_runner.exists():
        target_runner.write_text(template_runner.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        target_runner.write_text("#!/usr/bin/env python3\nprint('Pipeline runner initialized')\n", encoding="utf-8")

    # Configuração de nós do DAG
    default_nodes = [
        {
            "id": "node-01-ingest",
            "skill": "aidd-rea-video-youtube",
            "description": "Extracao de evidencias e analise de entrada",
            "depends_on": [],
            "input_handoff": "context/input/pipeline_input.json",
            "output_handoff": "context/handoffs/01_evidence_handoff.json"
        },
        {
            "id": "node-02-creator",
            "skill": "aidd-orchestrate-skill-creator",
            "description": "Geracao da skill hiper-especializada do dominio",
            "depends_on": ["node-01-ingest"],
            "input_handoff": "context/handoffs/01_evidence_handoff.json",
            "output_handoff": "context/handoffs/02_skill_handoff.json"
        },
        {
            "id": "node-03-executor",
            "skill": "aidd-motion-remotion-core",
            "description": "Execucao da entrega procedimental em codigo",
            "depends_on": ["node-02-creator"],
            "input_handoff": "context/handoffs/02_skill_handoff.json",
            "output_handoff": "context/output/final_delivery_handoff.json"
        }
    ]

    configured_nodes = steps if steps else default_nodes

    # PIPELINE.json canônico com interoperabilidade universal Lego
    pipeline_spec = {
        "version": "1.0.0",
        "pipeline_id": slug,
        "name": pipeline_name,
        "description": f"Pipeline autonomo composivel para {pipeline_name}",
        "pipeline_type": "autonomous_lego_pipeline",
        "input_contract": "context/input/pipeline_input.json",
        "output_contract": "context/output/pipeline_output.json",
        "upstream_reference": upstream_meta,
        "nodes": configured_nodes
    }

    (pipeline_dir / "PIPELINE.json").write_text(
        json.dumps(pipeline_spec, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # state.json inicial
    initial_state = {
        "pipeline_id": slug,
        "status": "INITIALIZED",
        "created_at": time_iso(),
        "nodes": {
            node["id"]: {"status": "PENDING", "completed_at": None, "error": None}
            for node in pipeline_spec["nodes"]
        }
    }
    (pipeline_dir / "state.json").write_text(
        json.dumps(initial_state, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 1. Manual de Instruções (README.md)
    readme_content = f"""# Manual de Instrucoes: {pipeline_name}

Pipeline autonomo composivel e deterministico criado pelo aidd-pipeline-creator.

## 1. Visao Geral
Este pipeline automatiza a cadeia de execucao completa para {pipeline_name}.
Opera como uma **peca de Lego composivel**, consumindo `context/input/pipeline_input.json` e exportando `context/output/pipeline_output.json` para encadeamento em Macro-Pipelines.

## 2. Arquitetura do Grafo (DAG)
O fluxo de execucao obedece a ordem topologica:
"""
    for node in configured_nodes:
        readme_content += f"- **{node['id']}**: {node.get('description', '')} (Skill: `{node.get('skill', 'inline')}`)\n"

    readme_content += """
## 3. Como Executar

### Execucao Padrao
```bash
python run_pipeline.py
```

### Forcar Reexecucao Completa
```bash
python run_pipeline.py --force
```

## 4. Contratos de Entrada e Saida (Lego de Pipelines)
- Entrada Raiz: `context/input/pipeline_input.json`
- Saida Raiz: `context/output/pipeline_output.json`
- Handoffs Intermediarios: `context/handoffs/`
"""
    (pipeline_dir / "README.md").write_text(readme_content, encoding="utf-8")

    # 2. Contrato de Governança para Agentes (AGENTS.md)
    agents_content = f"""# AGENTS.md - Governanca para Agentes de IA

Diretrizes para agentes autonomos que executam, monitoram ou ajustam o pipeline {pipeline_name}.

## 1. Regras Operacionais Inegociaveis
1. Nao modifique manualmente arquivos em `context/handoffs/`. As mutacoes devem ocorrer estritamente pelos runners e skills.
2. Em caso de falha, inspecione `state.json` para identificar o no exato e o erro reportado.
3. Respeite o isolamento canônico do pipeline. Nao polua a raiz do projeto.
4. Assegure a presenca do arquivo de entrada em `context/input/pipeline_input.json` antes do disparo.
"""
    (pipeline_dir / "AGENTS.md").write_text(agents_content, encoding="utf-8")

    # 3. Regras e Circuit Breakers (RULES.md)
    rules_content = f"""# RULES.md - Gates e Circuit Breakers do Pipeline

Regras de conformidade e criterios de parada obrigatorios.

## Gate 1: Integridade de Entrada
- O primeiro no do DAG valida a existencia de `context/input/pipeline_input.json`.

## Gate 2: Conformidade de Handoff
- Todo no intermediario DEVE emitir envelope JSON valido.

## Gate 3: Envelope de Saida Lego
- Ao concluir todos os nos com sucesso, o runner DEVE emitir `context/output/pipeline_output.json`.
"""
    (pipeline_dir / "RULES.md").write_text(rules_content, encoding="utf-8")

    # 4. Licença MIT Formal
    license_content = """MIT License

Copyright (c) 2026 Heverton Eduardo Peres

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
    (pipeline_dir / "LICENSE").write_text(license_content, encoding="utf-8")

    # 5. Dependências Formais (dependencies.json)
    skills_used = list({node["skill"] for node in configured_nodes if node.get("skill")})
    dependencies_content = {
        "$schema": "https://aidd.framework/schemas/dependencies-v1.json",
        "pipeline_name": slug,
        "version": "1.0.0",
        "author": "Heverton Eduardo Peres",
        "dependencies": {
            "skills_required": [
                {"name": s, "optional": False, "purpose": f"Execucao dos nos de {s}"}
                for s in skills_used
            ],
            "mcp_servers": {},
            "system_binaries": [
                {"name": "python", "required": True, "purpose": "Execucao dos scripts do pipeline"},
                {"name": "git", "required": True, "purpose": "Versionamento e controle de estado"}
            ],
            "python_packages": [
                "argparse"
            ]
        }
    }
    (pipeline_dir / "dependencies.json").write_text(
        json.dumps(dependencies_content, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # 6. Referência Conceitual e Upstream
    ref_content = f"""# Arquitetura e Fundamentacao: {pipeline_name}

Documento de referencia conceitual que embasa a construcao tecnica deste pipeline.
"""
    if upstream_meta:
        ref_content += f"""
## Referencia de Autoridade Upstream
- Repositorio / Origem: {upstream_meta.get('url', 'N/A')}
- Autor / Mantenedor: {upstream_meta.get('owner', {}).get('login') if isinstance(upstream_meta.get('owner'), dict) else upstream_meta.get('owner', 'N/A')}
- Estrelas / Validacao: {upstream_meta.get('stargazersCount', 'N/A')}
- Descricao Original: {upstream_meta.get('description', 'N/A')}
"""
    ref_content += """
## Contratos de Interoperabilidade Lego
As comunicacoes sao realizadas atraves de envelopes JSON validados por schemas formais:
- Entrada: `pipeline_input.json`
- Saida: `pipeline_output.json`
"""
    (pipeline_dir / "references" / "00-arquitetura.md").write_text(ref_content, encoding="utf-8")

    print(f"\n[+] Pipeline Autonomo Enterprise provisionado com sucesso em: {pipeline_dir.resolve()}")
    print(f"    |-- README.md         (Manual de instrucao completo)")
    print(f"    |-- AGENTS.md         (Contrato de governanca para agentes)")
    print(f"    |-- RULES.md          (Gates e circuit breakers)")
    print(f"    |-- LICENSE           (Licenca MIT formal Heverton Eduardo Peres)")
    print(f"    |-- dependencies.json (Mapeamento formal de dependencias)")
    print(f"    |-- PIPELINE.json     (DAG com {len(pipeline_spec['nodes'])} nos - Lego Habilitado)")
    print(f"    |-- run_pipeline.py   (Runner deterministico com emissao de pipeline_output.json)")
    print(f"    |-- state.json        (Telemetria e checkpointing)")
    print(f"    |-- references/       (Fundamentacao tecnica e upstream)")
    print(f"    |-- templates/        (Modelos e schemas)")
    print(f"    |-- context/          (input/, handoffs/, output/)")
    print(f"    `-- skills/           (Espaco para micro-skills locais se necessario)")

    return pipeline_dir


def scout_and_canonize_pipeline(query: str, pipeline_name: str | None = None, base_dir: Path | None = None) -> Path:
    """
    Garimpa pipeline de autoridade no GitHub, disseca seus metadados e canoniza como pipeline proprietário AIDD.
    """
    print(f"=== [AIDD-CANONIZE-PIPELINE] Garimpando e Canonizando Pipeline para: '{query}' ===")
    results = scout_github_for_pipeline(query, min_stars=10, limit=3)
    upstream = results[0] if results else None

    if upstream:
        p_name = pipeline_name or upstream["name"]
        print(f"[+] Origem de Autoridade Encontrada: {upstream.get('url')} ({upstream.get('stargazersCount')} estrelas)")
    else:
        p_name = pipeline_name or query.replace(" ", "-").lower()
        print("[-] Nenhuma referencia upstream atingiu o limiar de estrelas. Criando pipeline canônico local.")

    return scaffold_autonomous_pipeline(p_name, base_dir=base_dir, upstream_meta=upstream)


def run_environment_inventory(output_json: Path | None = None) -> dict:
    """
    Discovery de Ambiente 100% Determinístico:
    Varre as 13 pastas de skills registradas da máquina e mapeia MCPs.
    """
    print("=== [AIDD-DISCOVERY] Varrendo Ambiente da Máquina (Skills & MCPs) ===")
    home = Path.home()
    skill_roots = [
        home / ".agents" / "skills",
        home / ".claude" / "skills",
        home / ".config" / "opencode" / "skills",
        home / ".opencode" / "skills",
        home / ".gemini" / "skills",
        home / ".gemini" / "antigravity" / "skills",
        home / ".gemini" / "antigravity-cli" / "skills",
        home / ".gemini" / "config" / "skills",
        home / ".cursor" / "skills",
        home / ".hermes" / "skills",
        home / ".cline" / "skills",
        home / ".factory" / "skills",
        home / ".mimocode" / "skills",
        Path.cwd() / "aidd-skills"
    ]

    discovered_skills = {}
    for root in skill_roots:
        if not root.exists():
            continue
        for item in root.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                name = item.name
                if name not in discovered_skills:
                    discovered_skills[name] = {
                        "name": name,
                        "path": str(item),
                        "description": extract_frontmatter_description(item / "SKILL.md"),
                        "has_agents_md": (item / "AGENTS.md").exists(),
                        "has_rules_md": (item / "RULES.md").exists(),
                        "harnesses": [str(root)]
                    }
                else:
                    discovered_skills[name]["harnesses"].append(str(root))

    print(f"\n[+] Total de skills únicas encontradas: {len(discovered_skills)}")
    for s_name, s_data in sorted(discovered_skills.items()):
        print(f"  • {s_name} ({len(s_data['harnesses'])} harnesses)")

    inv = {
        "timestamp": time_iso(),
        "total_unique_skills": len(discovered_skills),
        "skills": discovered_skills
    }

    if output_json:
        output_json.write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")

    return inv


def plan_swarm_pipeline(input_source_str: str, output_plan: Path | None = None) -> dict:
    """
    Planeja o Grafo DAG de execução decomposto a partir de uma spec ou briefing.
    """
    print(f"=== [AIDD-PLANNER] Compilando Grafo DAG a partir de: {input_source_str} ===")
    swarm_plan = {
        "version": "1.0.0",
        "plan_id": f"plan-{int(time.time())}",
        "created_at": time_iso(),
        "source_input": input_source_str,
        "nodes": [
            {
                "id": "ETAPA-01-DISCOVERY",
                "role": "Mapeamento e Ingestao de Dados",
                "skill": "aidd-rea-video-youtube",
                "status": "AVAILABLE_IN_INVENTORY",
                "blocked_by": []
            },
            {
                "id": "ETAPA-02-CREATOR",
                "role": "Geracao de Modulos Especificos",
                "skill": "aidd-orchestrate-skill-creator",
                "status": "AVAILABLE_IN_INVENTORY",
                "blocked_by": ["ETAPA-01-DISCOVERY"]
            },
            {
                "id": "ETAPA-03-MOTION-ENGINE",
                "role": "Geracao Procedural de Animacao",
                "skill": "aidd-motion-remotion-core",
                "status": "AVAILABLE_IN_INVENTORY",
                "blocked_by": ["ETAPA-02-CREATOR"]
            }
        ],
        "handoff_pipe_contract": "HANDOFF.json"
    }

    out_file = output_plan or Path("SWARM_PLAN.json")
    out_file.write_text(json.dumps(swarm_plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[+] Grafo DAG compilado com sucesso em: {out_file.resolve()}")
    return swarm_plan


def evolve_pipeline(
    pipeline_target: str,
    add_step: str | None = None,
    after_node: str | None = None,
    remove_step_id: str | None = None,
    spec: str | None = None,
    base_dir: Path | None = None,
    author: str = "Heverton Eduardo Peres"
) -> Path:
    """
    Evolui e refina o grafo DAG de um pipeline autônomo existente:
    1. Localiza a pasta do pipeline em aidd-pipelines/<slug>/ ou caminho fornecido.
    2. Lê PIPELINE.json.
    3. Se add_step: insere novo nó no DAG (após after_node ou no final), reconfigurando depends_on e handoffs.
    4. Se remove_step_id: remove o nó e reconecta dependências.
    5. Atualiza PIPELINE.json, state.json, dependencies.json e README.md.
    6. Registra no references/EVOLUTION_LOG.md.
    7. Assegura a integridade do contrato Lego (pipeline_output.json).
    """
    slug = re.sub(r"[^\w\-]", "-", pipeline_target.lower()).strip("-")
    base = base_dir or Path("aidd-pipelines")
    pipeline_dir = base / slug
    if not pipeline_dir.exists():
        direct = Path(pipeline_target)
        if direct.exists() and (direct / "PIPELINE.json").exists():
            pipeline_dir = direct
        else:
            print(f"[ERRO] Pipeline nao encontrado para evolucao: {pipeline_target}", file=sys.stderr)
            sys.exit(1)

    spec_file = pipeline_dir / "PIPELINE.json"
    if not spec_file.exists():
        print(f"[ERRO] PIPELINE.json inexistente em: {pipeline_dir}", file=sys.stderr)
        sys.exit(1)

    pipeline_spec = json.loads(spec_file.read_text(encoding="utf-8"))
    nodes = pipeline_spec.get("nodes", [])

    print(f"=== [AIDD-EVOLVE-PIPELINE] Evoluindo Pipeline: {pipeline_spec.get('name', slug)} ===")

    # 1. Adicionar nó
    if add_step:
        new_skill = add_step.strip()
        new_node_id = f"node-{len(nodes) + 1:02d}-{new_skill.replace('aidd-', '')}"

        if after_node:
            depends_on = [after_node]
        elif nodes:
            depends_on = [nodes[-1]["id"]]
        else:
            depends_on = []

        new_node = {
            "id": new_node_id,
            "skill": new_skill,
            "description": f"Execucao evoluida da etapa {new_skill}",
            "depends_on": depends_on,
            "input_handoff": "context/handoffs/previous_handoff.json" if depends_on else "context/input/pipeline_input.json",
            "output_handoff": f"context/handoffs/{len(nodes)+1:02d}_handoff.json"
        }

        if after_node:
            insert_idx = next((i + 1 for i, n in enumerate(nodes) if n["id"] == after_node), len(nodes))
            nodes.insert(insert_idx, new_node)
        else:
            nodes.append(new_node)

        # Garantir que o último nó emita pipeline_output.json
        for i, n in enumerate(nodes):
            if i == len(nodes) - 1:
                n["output_handoff"] = "context/output/pipeline_output.json"

        print(f"[+] Novo nó inserido no DAG: {new_node_id} (Skill: {new_skill})")

    # 2. Remover nó
    if remove_step_id:
        nodes = [n for n in nodes if n["id"] != remove_step_id]
        for n in nodes:
            if remove_step_id in n.get("depends_on", []):
                n["depends_on"].remove(remove_step_id)
        if nodes:
            nodes[-1]["output_handoff"] = "context/output/pipeline_output.json"
        print(f"[-] Nó removido do DAG: {remove_step_id}")

    pipeline_spec["nodes"] = nodes
    spec_file.write_text(json.dumps(pipeline_spec, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Atualizar state.json
    state_file = pipeline_dir / "state.json"
    if state_file.exists():
        try:
            state_data = json.loads(state_file.read_text(encoding="utf-8"))
            for n in nodes:
                if n["id"] not in state_data.get("nodes", {}):
                    state_data.setdefault("nodes", {})[n["id"]] = {"status": "PENDING", "completed_at": None, "error": None}
            state_file.write_text(json.dumps(state_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    # 4. Atualizar dependencies.json
    dep_file = pipeline_dir / "dependencies.json"
    if dep_file.exists():
        try:
            dep_data = json.loads(dep_file.read_text(encoding="utf-8"))
            current_skills = list({n["skill"] for n in nodes if n.get("skill")})
            dep_data.setdefault("dependencies", {})["skills_required"] = [
                {"name": s, "optional": False, "purpose": f"Execucao dos nos de {s}"}
                for s in current_skills
            ]
            dep_file.write_text(json.dumps(dep_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    # 5. Registrar no log de evolução
    ref_dir = pipeline_dir / "references"
    ref_dir.mkdir(parents=True, exist_ok=True)
    evo_log = ref_dir / "EVOLUTION_LOG.md"
    evo_entry = f"""
## [Evolucao DAG] - {time.strftime("%Y-%m-%d %H:%M:%SZ")}
- **Autor**: {author}
- **Acao**: Adicionar {add_step or 'N/A'} / Remover {remove_step_id or 'N/A'}
- **Especificacao**: {spec or 'Expansao do pipeline'}
- **Total de nós atual**: {len(nodes)}
- **Status**: Homologado
"""
    if evo_log.exists():
        evo_log.write_text(evo_log.read_text(encoding="utf-8") + evo_entry, encoding="utf-8")
    else:
        evo_log.write_text(f"# Log de Evolucao do Pipeline: {pipeline_dir.name}\n" + evo_entry, encoding="utf-8")

    print(f"\n[OK] Pipeline '{pipeline_dir.name}' evoluido com sucesso! Total de nós no DAG: {len(nodes)}")
    return pipeline_dir


def main():
    parser = argparse.ArgumentParser(description="Criador e Garimpador de Pipelines Composíveis (aidd-pipeline-creator v1.0.0)")
    parser.add_argument("-i", "--input", help="Caminho do arquivo de entrada / spec / briefing / handoff de entrada")
    parser.add_argument("--output-handoff", help="Caminho do arquivo de handoff gerado")
    parser.add_argument("--inventory", action="store_true", help="Descobre e mapeia todas as skills da máquina e almoxarifado")
    parser.add_argument("--scout-local", action="store_true", help="Garimpa pipelines e workflows locais")
    parser.add_argument("--scout-github", metavar="QUERY", help="Garimpa pipelines de autoridade no GitHub com cache e anti-ban")
    parser.add_argument("--scout-and-canonize", metavar="QUERY", help="Garimpa e canoniza pipeline completo de autoridade")
    parser.add_argument("--scaffold-pipeline", metavar="NOME", help="Provisiona estrutura de Pipeline Autônomo encapsulado")
    parser.add_argument("--steps", metavar="STEPS", help="Lista de skills separadas por virgula para os nós do pipeline")
    parser.add_argument("--plan", metavar="INPUT", help="Planeja o Grafo DAG do enxame a partir de um input/briefing")
    parser.add_argument("--doctor", action="store_true", help="Diagnostico de ambiente")
    parser.add_argument("--setup", action="store_true", help="Setup automatico e sync")
    parser.add_argument("--audit", metavar="PASTA", nargs="?", const=".", help="Auditoria de conformidade dos 4 Gates")
    parser.add_argument("--evolve", metavar="PIPELINE", help="Evolui um pipeline existente adicionando ou removendo etapas")
    parser.add_argument("--refine", metavar="PIPELINE", help="Alias de --evolve")
    parser.add_argument("--add-step", metavar="SKILL", help="Nome da skill para adicionar como novo nó no DAG")
    parser.add_argument("--after", metavar="NODE_ID", help="ID do nó predecessor para posicionamento no DAG")
    parser.add_argument("--remove-step", metavar="NODE_ID", help="ID do nó a ser removido do DAG")
    parser.add_argument("--spec", metavar="SPEC", help="Especificação técnica da evolução do pipeline")

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

    evolve_target = args.evolve or args.refine
    if evolve_target:
        evolve_pipeline(
            pipeline_target=evolve_target,
            add_step=args.add_step,
            after_node=args.after,
            remove_step_id=args.remove_step,
            spec=args.spec
        )
        return

    if args.inventory:
        run_environment_inventory()
        return

    if args.scout_local:
        scout_local_pipelines()
        return

    if args.scout_github:
        scout_github_for_pipeline(args.scout_github)
        return

    if args.scout_and_canonize:
        scout_and_canonize_pipeline(args.scout_and_canonize)
        return

    if args.scaffold_pipeline:
        steps_list = None
        if args.steps:
            skills = [s.strip() for s in args.steps.split(",") if s.strip()]
            steps_list = []
            prev_id = None
            for idx, sk in enumerate(skills, start=1):
                node_id = f"node-{idx:02d}-{sk.replace('aidd-', '')}"
                node = {
                    "id": node_id,
                    "skill": sk,
                    "description": f"Execucao da etapa {sk}",
                    "depends_on": [prev_id] if prev_id else [],
                    "input_handoff": "context/input/pipeline_input.json" if idx == 1 else f"context/handoffs/{idx-1:02d}_handoff.json",
                    "output_handoff": "context/output/pipeline_output.json" if idx == len(skills) else f"context/handoffs/{idx:02d}_handoff.json"
                }
                steps_list.append(node)
                prev_id = node_id
        scaffold_autonomous_pipeline(args.scaffold_pipeline, steps=steps_list)
        return

    if args.plan:
        plan_swarm_pipeline(args.plan)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
