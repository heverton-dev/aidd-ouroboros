#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ouroboros_master.py — Orquestrador deterministico do meta-fluxo AIDD-Ouroboros
Autor: Heverton Eduardo Peres (2026)
Padrão: AIDD Universal Architecture / Zero Stubs / Pointer Architecture / HMAC-SHA256

Fases:
  F1 (interativa, agente): entrevista → SPEC_PIPELINE.json (approved=true)
  F2 (autonoma, este script): --orchestrate <spec>
    1. valida spec contra schema
    2. rea_router (se houver target)
    3. skill_creator para skills ausentes (reuse/scout/create)
    4. dependency_resolver nos manifests
    5. pipeline_creator --scaffold-pipeline + --steps
    6. audit_runner

Exit codes:
  0 ok | 1 erro | 2 spec nao aprovada | 3 duvida (pending_question.json)
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jsonschema

SKILL_HOME = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_HOME.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from motores.governanca.credentials import carregar_env_local  # noqa: E402
from motores.governanca.handoff_crypto import criar_envelope_handoff  # noqa: E402

SPEC_SCHEMA_PATH = REPO_ROOT / "schemas" / "SPEC_PIPELINE.schema.json"
SPEC_TEMPLATE_PATH = REPO_ROOT / "schemas" / "SPEC_PIPELINE.template.json"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_NOT_APPROVED = 2
EXIT_NEEDS_INTERVIEW = 3

_STATE_ROOT = Path.cwd()
PENDING_QUESTION = _STATE_ROOT / "pending_question.json"
RUN_STATE_PATH = _STATE_ROOT / "ouroboros_master_state.json"


def set_runtime_root(out_dir: Path) -> None:
    global _STATE_ROOT, PENDING_QUESTION, RUN_STATE_PATH
    _STATE_ROOT = out_dir
    PENDING_QUESTION = _STATE_ROOT / "pending_question.json"
    RUN_STATE_PATH = _STATE_ROOT / "ouroboros_master_state.json"


def time_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def repo_tool(*relative: str) -> Path:
    return REPO_ROOT.joinpath(*relative)


def skill_exists(name: str) -> bool:
    return (repo_tool("aidd-skills", name, "SKILL.md")).is_file()


def run_cmd(cmd: List[str], cwd: Optional[Path] = None, timeout: int = 180) -> Tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return 124, f"timeout apos {timeout}s: {' '.join(cmd)}"
    except FileNotFoundError as exc:
        return 127, f"binario nao encontrado: {exc}"


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"JSON raiz deve ser objeto: {path}")
    return data


def emit_pending_question(question: str, context: str, stage: str) -> None:
    write_json(
        PENDING_QUESTION,
        {
            "stage": stage,
            "question": question,
            "context": context,
            "created_at": time_iso(),
            "instruction": "Reabra mini-entrevista, responda, atualize a SPEC e rode --orchestrate novamente com --resume.",
        },
    )


def save_state(state: Dict[str, Any]) -> None:
    write_json(RUN_STATE_PATH, state)


def load_state() -> Dict[str, Any]:
    if RUN_STATE_PATH.is_file():
        try:
            return load_json(RUN_STATE_PATH)
        except (json.JSONDecodeError, ValueError):
            return {}
    return {}


def pending_question_path() -> Path:
    return PENDING_QUESTION


def run_state_path() -> Path:
    return RUN_STATE_PATH


def validate_spec(spec: Dict[str, Any]) -> List[str]:
    if not SPEC_SCHEMA_PATH.is_file():
        return [f"schema ausente: {SPEC_SCHEMA_PATH}"]
    schema = load_json(SPEC_SCHEMA_PATH)
    validator = jsonschema.Draft7Validator(schema)
    return [f"{'/'.join(str(p) for p in err.path) or '<root>'}: {err.message}" for err in validator.iter_errors(spec)]


def spec_is_placeholder(spec: Dict[str, Any]) -> bool:
    req = str(spec.get("user_request", ""))
    pipeline = spec.get("pipeline") or {}
    name = str(pipeline.get("name", ""))
    if "PREENCHER" in req or req.strip() in {"", "PREENCHER: pedido em linguagem natural do usuario"}:
        return True
    if name in {"", "placeholder-pipeline"}:
        return True
    return False


def ensure_hmac_env() -> None:
    carregar_env_local()
    if not (os.environ.get("AIDD_HANDOFF_KEY") or os.environ.get("OUROBOROS_HMAC_SECRET")):
        secret = os.environ.get("OUROBOROS_CRYPTO_SECRET")
        if secret:
            os.environ["OUROBOROS_HMAC_SECRET"] = secret


def check_doctor() -> bool:
    print("=" * 70)
    print(" [AIDD-OUROBOROS-MASTER] Doctor — pré-voo do meta-fluxo")
    print("=" * 70)
    ok = True
    for tool, required in (("python", True), ("git", True), ("gh", False)):
        found = shutil.which(tool)
        print(f" [{'+' if found else ('!' if required else '-')}] {tool}: {'OK' if found else 'AUSENTE'}")
        if required and not found:
            ok = False

    specialists = [
        "aidd-rea-router",
        "aidd-rea-web-saas",
        "aidd-rea-app-android",
        "aidd-rea-video-youtube",
        "aidd-rea-social-carousel",
        "aidd-orchestrate-skill-creator",
        "aidd-orchestrate-pipeline-creator",
    ]
    for name in specialists:
        present = skill_exists(name)
        print(f" [{'+' if present else '!'}] skill {name}: {'OK' if present else 'AUSENTE'}")
        if not present:
            ok = False

    tools = [
        repo_tool("motores", "governanca", "audit_runner.py"),
        repo_tool("motores", "governanca", "dependency_resolver.py"),
        repo_tool("aidd-skills", "aidd-rea-router", "scripts", "rea_router.py"),
        repo_tool("aidd-skills", "aidd-orchestrate-skill-creator", "scripts", "skill_creator.py"),
        repo_tool("aidd-skills", "aidd-orchestrate-pipeline-creator", "scripts", "pipeline_creator.py"),
        SPEC_SCHEMA_PATH,
    ]
    for path in tools:
        present = path.is_file()
        print(f" [{'+' if present else '!'}] {path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path}: {'OK' if present else 'AUSENTE'}")
        if not present:
            ok = False

    ensure_hmac_env()
    has_key = bool(os.environ.get("AIDD_HANDOFF_KEY") or os.environ.get("OUROBOROS_HMAC_SECRET"))
    print(f" [{'+' if has_key else '!'}] HMAC handoff key: {'OK' if has_key else 'AUSENTE (defina OUROBOROS_CRYPTO_SECRET no .env)'}")
    if not has_key:
        ok = False

    print("-" * 70)
    print("[OK] Master pronta para F1+F2." if ok else "[!] Corrija os itens marcados com !.")
    return ok


def run_setup() -> bool:
    print("=" * 70)
    print(" [AIDD-OUROBOROS-MASTER] Setup — deps + sync")
    print("=" * 70)
    ensure_hmac_env()
    ok = True
    req = SKILL_HOME / "requirements.txt"
    if req.is_file():
        rc, out = run_cmd([sys.executable, "-m", "pip", "install", "-q", "-r", str(req)])
        print(out or "[+] requirements.txt instalado")
        if rc != 0:
            ok = False

    sync = SKILL_HOME / ("sync.ps1" if os.name == "nt" else "sync.sh")
    if sync.is_file():
        if os.name == "nt":
            rc, out = run_cmd(["powershell", "-ExecutionPolicy", "Bypass", "-File", str(sync)])
        else:
            rc, out = run_cmd(["bash", str(sync)])
        print(out or "[+] skills sincronizadas")
        if rc != 0:
            ok = False

    print("[OK] Setup concluído." if ok else "[!] Setup com falhas.")
    return ok


def run_audit() -> bool:
    print("=" * 70)
    print(" [AIDD-OUROBOROS-MASTER] Audit — gates desta skill")
    print("=" * 70)
    errors: List[str] = []

    skill_md = SKILL_HOME / "SKILL.md"
    if not skill_md.is_file():
        errors.append("SKILL.md ausente")
    else:
        content = skill_md.read_text(encoding="utf-8")
        m = re.search(r"^description:\s*(.+)$", content, re.MULTILINE)
        if not m:
            errors.append("frontmatter sem description")
        else:
            words = len(re.findall(r"\b[\w-]+\b", m.group(1)))
            if words > 25:
                errors.append(f"description com {words} palavras (max 25)")

    for required in ("AGENTS.md", "RULES.md", "LICENSE", "pyproject.toml", "dependencies.json", "README.md"):
        if not (SKILL_HOME / required).is_file():
            errors.append(f"{required} ausente")

    script = SKILL_HOME / "scripts" / "ouroboros_master.py"
    if not script.is_file():
        errors.append("scripts/ouroboros_master.py ausente")
    else:
        code = script.read_text(encoding="utf-8")
        for flag in ("--doctor", "--setup", "--audit", "--orchestrate", "--init-spec"):
            if flag not in code:
                errors.append(f"script nao implementa {flag}")

    gate_ast = repo_tool("motores", "governanca", "gate_ast.py")
    if gate_ast.is_file():
        rc, out = run_cmd([sys.executable, str(gate_ast), str(SKILL_HOME)])
        print(out)
        if rc != 0:
            errors.append("gate_ast falhou")

    if errors:
        for e in errors:
            print(f" [!] {e}", file=sys.stderr)
        return False

    print("[OK] Todos os gates da master passaram.")
    return True


def cmd_init_spec(output: Path, user_request: str = "", goal: str = "") -> int:
    if not SPEC_TEMPLATE_PATH.is_file():
        print(f"[!] Template ausente: {SPEC_TEMPLATE_PATH}", file=sys.stderr)
        return EXIT_ERROR

    template = load_json(SPEC_TEMPLATE_PATH)
    req = user_request.strip() or template["user_request"]
    digest = hashlib.sha256(f"{req}{time_iso()}".encode("utf-8")).hexdigest()[:16]
    template["spec_id"] = f"spec-{digest}"
    template["user_request"] = req
    template["goal"] = goal.strip() or template["goal"]
    template["created_at"] = time_iso()
    template["approved"] = False
    write_json(output, template)
    print(json.dumps(template, indent=2, ensure_ascii=False))
    print(f"[OK] Spec inicial escrita em {output}", file=sys.stderr)
    print("[*] F1: responda a entrevista, preencha a spec, marque approved=true e rode --orchestrate.", file=sys.stderr)
    return EXIT_OK


def target_uri(spec: Dict[str, Any]) -> Optional[str]:
    target = spec.get("target") or {}
    kind = target.get("kind", "none")
    if kind == "none":
        return None
    uri = target.get("uri") or target.get("path") or ""
    return uri.strip() or None


def stage_rea(spec: Dict[str, Any], state: Dict[str, Any], out_dir: Path) -> Tuple[bool, Optional[str]]:
    uri = target_uri(spec)
    if not uri:
        state["stages"]["rea"] = {"status": "SKIPPED", "reason": "sem target"}
        return True, None

    router = repo_tool("aidd-skills", "aidd-rea-router", "scripts", "rea_router.py")
    # Paths absolutos: subprocessos REA resolvem relativos a partir do cwd do skill,
    # o que deslocaria o handoff para aidd-skills/<skill>/<path>
    handoff = (out_dir / "handoffs" / "01_rea_handoff.json").resolve()
    rea_dir = (out_dir / "rea").resolve()
    handoff.parent.mkdir(parents=True, exist_ok=True)
    rea_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(router),
        "--target",
        uri,
        "--output-dir",
        str(rea_dir),
        "--output-handoff",
        str(handoff),
    ]
    rc, out = run_cmd(cmd, cwd=REPO_ROOT, timeout=300)
    print(out)
    if rc != 0:
        emit_pending_question(
            f"Falha ao rotear/disseccionar alvo '{uri}'. Clarifique o tipo de alvo ou forneça outro caminho/URL.",
            context=out[-2000:],
            stage="rea",
        )
        state["stages"]["rea"] = {"status": "FAILED", "rc": rc}
        return False, None

    if not handoff.is_file():
        emit_pending_question(
            f"REA nao emitiu handoff em {handoff}. Verifique o alvo e o dissecador.",
            context=out[-2000:],
            stage="rea",
        )
        state["stages"]["rea"] = {"status": "FAILED", "reason": "handoff ausente"}
        return False, None

    ensure_hmac_env()
    from motores.governanca.handoff_crypto import verify_handoff_envelope

    sig_ok, sig_msg = verify_handoff_envelope(handoff, verificar_integridade_disco=False)
    if not sig_ok:
        emit_pending_question(
            f"Handoff da REA falhou na verificacao HMAC: {sig_msg}. Reabra entrevista para regenerar o alvo.",
            context=str(handoff),
            stage="rea",
        )
        state["stages"]["rea"] = {"status": "FAILED", "reason": f"hmac: {sig_msg}"}
        return False, None

    state["stages"]["rea"] = {"status": "OK", "handoff": str(handoff), "hmac": "OK"}
    return True, str(handoff)


def resolve_skill(name: str, entry: Dict[str, Any], state: Dict[str, Any]) -> bool:
    if skill_exists(name):
        state["skills"][name] = {"action": "reuse", "status": "OK"}
        print(f" [+] skill reuse: {name}")
        return True

    mode = entry.get("mode", "create")
    creator = repo_tool("aidd-skills", "aidd-orchestrate-skill-creator", "scripts", "skill_creator.py")
    out_dir = repo_tool("aidd-skills")
    ensure_hmac_env()

    if mode == "github-scout":
        query = entry.get("github_query") or name
        cmd = [
            sys.executable,
            str(creator),
            "--github-scout",
            query,
            "--nome",
            name,
            "--output-dir",
            str(out_dir),
        ]
    else:
        cmd = [
            sys.executable,
            str(creator),
            "--nome",
            name,
            "--output-dir",
            str(out_dir),
        ]

    rc, out = run_cmd(cmd, cwd=REPO_ROOT, timeout=300)
    print(out)
    if rc != 0 or not skill_exists(name):
        emit_pending_question(
            f"Skill '{name}' nao pôde ser criada (modo={mode}). Deseja outro nome, outro scout GitHub ou criar manualmente?",
            context=out[-2000:],
            stage="skill_create",
        )
        state["skills"][name] = {"action": mode, "status": "FAILED", "rc": rc}
        return False

    state["skills"][name] = {"action": mode, "status": "OK"}
    print(f" [+] skill criada: {name}")
    return True


def stage_skills(spec: Dict[str, Any], state: Dict[str, Any]) -> bool:
    entries = spec.get("skills_required") or []
    if not entries:
        state["stages"]["skills"] = {"status": "SKIPPED"}
        return True

    for entry in entries:
        name = str(entry.get("name", "")).strip()
        if not name:
            emit_pending_question(" skills_required contem item sem name. Corrija a spec.", context=json.dumps(entry, ensure_ascii=False), stage="skills")
            return False
        if not resolve_skill(name, entry, state):
            return False

    state["stages"]["skills"] = {"status": "OK"}
    return True


def stage_dependencies(spec: Dict[str, Any], state: Dict[str, Any], pipeline_dir: Optional[Path]) -> bool:
    if not spec.get("install_dependencies", True):
        state["stages"]["dependencies"] = {"status": "SKIPPED"}
        return True

    resolver = repo_tool("motores", "governanca", "dependency_resolver.py")
    manifests: List[Path] = []
    if pipeline_dir and (pipeline_dir / "dependencies.json").is_file():
        manifests.append(pipeline_dir / "dependencies.json")
    for name in (spec.get("skills_required") or []):
        n = name.get("name") if isinstance(name, dict) else None
        if n:
            man = repo_tool("aidd-skills", str(n), "dependencies.json")
            if man.is_file():
                manifests.append(man)

    if not manifests:
        state["stages"]["dependencies"] = {"status": "SKIPPED", "reason": "sem manifests"}
        return True

    ensure_hmac_env()
    for man in manifests:
        rc, out = run_cmd([sys.executable, str(resolver), "--manifest", str(man), "--install", "--yes"], cwd=REPO_ROOT, timeout=600)
        print(f" [deps] {man.name}: rc={rc}")
        if out:
            print(out[-1500:])
        if rc != 0:
            state["stages"]["dependencies"] = {"status": "FAILED", "manifest": str(man), "rc": rc}
            emit_pending_question(
                f"Falha ao instalar dependencias de {man}. Continuar sem instalar ou ajustar versions?",
                context=out[-2000:],
                stage="dependencies",
            )
            return False

    state["stages"]["dependencies"] = {"status": "OK", "count": len(manifests)}
    return True


def stage_pipeline(spec: Dict[str, Any], state: Dict[str, Any], out_dir: Path) -> Tuple[bool, Optional[Path]]:
    pipeline = spec.get("pipeline") or {}
    name = str(pipeline.get("name", "")).strip()
    steps = pipeline.get("steps") or []
    if not name or not steps:
        emit_pending_question(
            "Spec sem pipeline.name ou pipeline.steps. Complete o DAG na entrevista.",
            context=json.dumps(pipeline, ensure_ascii=False)[:1500],
            stage="pipeline",
        )
        return False, None

    creator = repo_tool("aidd-skills", "aidd-orchestrate-pipeline-creator", "scripts", "pipeline_creator.py")
    slug = re.sub(r"[^\w\-]", "-", name.lower()).strip("-")

    skill_names = [str(step.get("skill", "")).strip() for step in steps if str(step.get("skill", "")).strip()]
    if not skill_names:
        emit_pending_question(
            "pipeline.steps sem skills validas.",
            context=json.dumps(steps, ensure_ascii=False)[:1500],
            stage="pipeline",
        )
        return False, None

    # pipeline_creator espera --steps como lista CSV de skills (nao JSON)
    steps_arg = ",".join(skill_names)
    scaffold_cwd = out_dir
    scaffold_cwd.mkdir(parents=True, exist_ok=True)
    cmd_scaffold = [
        sys.executable,
        str(creator),
        "--scaffold-pipeline",
        name,
        "--steps",
        steps_arg,
    ]
    rc, out = run_cmd(cmd_scaffold, cwd=scaffold_cwd, timeout=180)
    print(out)
    pipeline_dir = scaffold_cwd / "aidd-pipelines" / slug
    if rc != 0 or not pipeline_dir.is_dir():
        rc2, out2 = run_cmd(cmd_scaffold, cwd=REPO_ROOT, timeout=180)
        print(out2)
        if rc2 != 0:
            emit_pending_question(
                f"Falha ao scaffoldar pipeline '{name}'. Renomear ou ajustar steps?",
                context=(out + out2)[-2000:],
                stage="pipeline",
            )
            return False, None
        pipeline_dir = REPO_ROOT / "aidd-pipelines" / slug

    if not pipeline_dir.is_dir():
        emit_pending_question(
            f"Pipeline '{name}' nao encontrado apos scaffold.",
            context=str(pipeline_dir),
            stage="pipeline",
        )
        return False, None

    # Reescreve PIPELINE.json com o DAG rich da spec (IDs e depends_on)
    nodes = []
    for i, step in enumerate(steps, start=1):
        nodes.append(
            {
                "id": str(step.get("id") or f"node-{i:02d}"),
                "skill": str(step.get("skill", "")),
                "description": str(step.get("description", "")),
                "depends_on": list(step.get("depends_on") or []),
                "input_handoff": f"context/handoffs/{i:02d}_in.json",
                "output_handoff": f"context/handoffs/{i:02d}_out.json",
            }
        )
    pipe_json_path = pipeline_dir / "PIPELINE.json"
    if pipe_json_path.is_file():
        pipe_data = load_json(pipe_json_path)
        pipe_data["nodes"] = nodes
        pipe_data["name"] = name
        pipe_data["pipeline_id"] = slug
        write_json(pipe_json_path, pipe_data)

    state["stages"]["pipeline"] = {"status": "OK", "path": str(pipeline_dir)}
    return True, pipeline_dir


def stage_audit(out_dir: Path, state: Dict[str, Any]) -> bool:
    audit = repo_tool("motores", "governanca", "audit_runner.py")
    if not audit.is_file():
        state["stages"]["audit"] = {"status": "SKIPPED"}
        return True
    rc, out = run_cmd([sys.executable, str(audit), "--skip-pytest"], cwd=REPO_ROOT, timeout=180)
    print(out)
    state["stages"]["audit"] = {"status": "OK" if rc == 0 else "FAILED", "rc": rc}
    return rc == 0


def emit_final_handoff(spec: Dict[str, Any], state: Dict[str, Any], out_dir: Path) -> None:
    ensure_hmac_env()
    pipeline_path = (state.get("stages", {}).get("pipeline") or {}).get("path")
    artefatos: Dict[str, str] = {"state_path": str(RUN_STATE_PATH)}
    if pipeline_path:
        artefatos["pipeline_dir"] = str(pipeline_path)
    status = "SUCCESS" if state.get("status") == "OK" else "PARTIAL"
    metadados = {
        "spec_id": spec.get("spec_id"),
        "user_request": spec.get("user_request"),
        "goal": spec.get("goal"),
        "pipeline_name": (spec.get("pipeline") or {}).get("name"),
        "stages": state.get("stages", {}),
    }
    try:
        envelope = criar_envelope_handoff(
            origem_skill="aidd-ouroboros-master",
            status_ou_artefatos=status,
            artefatos_ou_metadados=artefatos,
            metadados=metadados,
            caminho_saida=out_dir / "handoffs" / "master_final_handoff.json",
        )
        print(f"[+] Handoff final emitido em {out_dir / 'handoffs' / 'master_final_handoff.json'}")
        print(json.dumps({"status": status, "spec_id": metadados.get("spec_id")}, ensure_ascii=False))
        del envelope
    except Exception as exc:
        print(f"[!] Handoff final nao emitido: {exc}", file=sys.stderr)


def orchestrate(spec_path: Path, resume: bool, out_dir: Path) -> int:
    if not spec_path.is_file():
        print(f"[!] Spec nao encontrada: {spec_path}", file=sys.stderr)
        return EXIT_ERROR

    try:
        spec = load_json(spec_path)
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"[!] JSON invalido: {exc}", file=sys.stderr)
        return EXIT_ERROR

    errors = validate_spec(spec)
    if errors:
        for e in errors:
            print(f" [schema] {e}", file=sys.stderr)
        return EXIT_ERROR

    if not spec.get("approved"):
        print("[!] Spec nao aprovada (approved=false). Complete a F1 (entrevista).", file=sys.stderr)
        return EXIT_NOT_APPROVED

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "handoffs").mkdir(parents=True, exist_ok=True)
    set_runtime_root(out_dir)

    if spec_is_placeholder(spec):
        print("[!] Spec contem placeholders. Preencha user_request e pipeline.name.", file=sys.stderr)
        emit_pending_question(
            "Spec ainda contem placeholders. Qual e o pedido real e o nome do pipeline?",
            context=json.dumps(spec, ensure_ascii=False)[:1500],
            stage="spec",
        )
        return EXIT_NEEDS_INTERVIEW

    state = load_state() if resume else {}
    state.update(
        {
            "spec_id": spec.get("spec_id"),
            "started_at": time_iso(),
            "status": "RUNNING",
            "stages": state.get("stages", {}),
            "skills": state.get("skills", {}),
        }
    )
    save_state(state)

    print("=" * 70)
    print(f" [AIDD-OUROBOROS-MASTER] Orquestração F2 — {spec.get('spec_id')}")
    print("=" * 70)

    ok_rea, _ = stage_rea(spec, state, out_dir)
    save_state(state)
    if not ok_rea:
        state["status"] = "NEEDS_INTERVIEW"
        save_state(state)
        return EXIT_NEEDS_INTERVIEW

    ok_skills = stage_skills(spec, state)
    save_state(state)
    if not ok_skills:
        state["status"] = "NEEDS_INTERVIEW"
        save_state(state)
        return EXIT_NEEDS_INTERVIEW

    ok_pipe, pipeline_dir = stage_pipeline(spec, state, out_dir)
    save_state(state)
    if not ok_pipe:
        state["status"] = "NEEDS_INTERVIEW"
        save_state(state)
        return EXIT_NEEDS_INTERVIEW

    ok_deps = stage_dependencies(spec, state, pipeline_dir)
    save_state(state)
    if not ok_deps:
        state["status"] = "NEEDS_INTERVIEW"
        save_state(state)
        return EXIT_NEEDS_INTERVIEW

    ok_audit = stage_audit(out_dir, state)
    save_state(state)

    state["status"] = "OK" if ok_audit else "PARTIAL"
    state["finished_at"] = time_iso()
    save_state(state)

    if ok_audit and PENDING_QUESTION.is_file():
        try:
            PENDING_QUESTION.unlink()
        except OSError as unlink_exc:
            print(f"[!] Nao foi possivel remover {PENDING_QUESTION.name}: {unlink_exc}", file=sys.stderr)

    emit_final_handoff(spec, state, out_dir)

    if ok_audit:
        print("[OK] Orquestracao F2 concluida com audit exit 0.")
        return EXIT_OK

    print("[!] Orquestracao parcial: audit falhou. Inspecione state.json.", file=sys.stderr)
    return EXIT_ERROR


def main() -> int:
    parser = argparse.ArgumentParser(description="Orquestrador mestre do meta-fluxo AIDD-Ouroboros")
    parser.add_argument("--doctor", action="store_true", help="Diagnostico do meta-fluxo")
    parser.add_argument("--setup", action="store_true", help="Instala deps e sincroniza skills")
    parser.add_argument("--audit", action="store_true", help="Audita anatomia e gates desta skill")
    parser.add_argument("--init-spec", action="store_true", help="Gera SPEC_PIPELINE.json template")
    parser.add_argument("--orchestrate", metavar="SPEC", help="Executa F2 a partir de SPEC_PIPELINE.json")
    parser.add_argument("--from-nl", metavar="TEXTO", help="Semeia spec a partir de pedido NL (F1 ainda exige aprovacao)")
    parser.add_argument("--output-spec", metavar="CAMINHO", default=str(Path.cwd() / "SPEC_PIPELINE.json"))
    parser.add_argument("--output-dir", metavar="DIR", default=str(Path.cwd() / "ouroboros-out"))
    parser.add_argument("--goal", metavar="GOAL", default="", help="Objetivo observavel para --init-spec/--from-nl")
    parser.add_argument("--resume", action="store_true", help="Retoma state.json anterior")
    args = parser.parse_args()

    if args.doctor:
        return EXIT_OK if check_doctor() else EXIT_ERROR
    if args.setup:
        return EXIT_OK if run_setup() else EXIT_ERROR
    if args.audit:
        return EXIT_OK if run_audit() else EXIT_ERROR

    out_spec = Path(args.output_spec)
    out_dir = Path(args.output_dir)

    if args.from_nl:
        return cmd_init_spec(out_spec, user_request=args.from_nl, goal=args.goal)

    if args.init_spec:
        return cmd_init_spec(out_spec, goal=args.goal)

    if args.orchestrate:
        return orchestrate(Path(args.orchestrate), resume=args.resume, out_dir=out_dir)

    parser.print_help()
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
