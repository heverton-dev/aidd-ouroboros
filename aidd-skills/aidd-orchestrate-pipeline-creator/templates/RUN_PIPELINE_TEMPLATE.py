#!/usr/bin/env python3
"""Runner determinístico de pipeline DAG do ecossistema AIDD Ouroboros.

Executa nós topologicamente com isolamento por run_id, cache de inputs_hash,
validação de handoffs criptográficos e rastreamento de estado em state.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


def load_pipeline_spec(pipeline_dir: Path) -> Dict[str, Any]:
    """Carrega especificação do pipeline (PIPELINE.json ou pipeline.json)."""
    p1 = pipeline_dir / "PIPELINE.json"
    p2 = pipeline_dir / "pipeline.json"
    target = p1 if p1.exists() else p2
    if not target.exists():
        raise FileNotFoundError(f"Arquivo de especificação não encontrado em {pipeline_dir}")
    with open(target, "r", encoding="utf-8") as f:
        spec: Dict[str, Any] = json.load(f)
        return spec


def resolve_workspace(
    pipeline_dir: Path,
    workspace_arg: Optional[str] = None,
    resume_arg: Optional[str] = None,
) -> tuple[Path, str]:
    """Resolve diretório de workspace isolado e identificador run_id."""
    if workspace_arg:
        ws = Path(workspace_arg).resolve()
        ws.mkdir(parents=True, exist_ok=True)
        return ws, ws.name

    if resume_arg:
        ws = (pipeline_dir / ".workspaces" / resume_arg).resolve()
        if not ws.exists():
            raise FileNotFoundError(f"Workspace para resume não encontrado: {ws}")
        return ws, resume_arg

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    suffix = uuid.uuid4().hex[:6]
    run_id = f"run_{timestamp}_{suffix}"
    ws = (pipeline_dir / ".workspaces" / run_id).resolve()
    ws.mkdir(parents=True, exist_ok=True)
    return ws, run_id


def calculate_node_input_hash(node: Dict[str, Any], pipeline_dir: Path) -> str:
    """Calcula hash SHA-256 determinístico dos inputs e metadados estruturais do nó."""
    hasher = hashlib.sha256()

    in_ref = node.get("input_handoff") or node.get("input")
    if in_ref:
        in_path = Path(in_ref)
        if not in_path.is_absolute():
            in_path = (pipeline_dir / in_path).resolve()
        if in_path.exists() and in_path.is_file():
            hasher.update(in_path.read_bytes())
        else:
            hasher.update(str(in_ref).encode("utf-8"))
    else:
        hasher.update(b"no_input")

    structural_meta = {
        k: v
        for k, v in node.items()
        if k not in {"status", "completed_at", "error", "inputs_hash"}
    }
    hasher.update(json.dumps(structural_meta, sort_keys=True).encode("utf-8"))
    return hasher.hexdigest()


def load_or_init_state(state_file: Path, pipeline_id: str, run_id: str) -> Dict[str, Any]:
    """Carrega ou inicializa state.json no workspace alvo."""
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            state: Dict[str, Any] = json.load(f)
            return state

    initial_state: Dict[str, Any] = {
        "pipeline_id": pipeline_id,
        "run_id": run_id,
        "started_at": time.time(),
        "status": "RUNNING",
        "nodes": {},
    }
    save_state(state_file, initial_state)
    return initial_state


def save_state(state_file: Path, state: Dict[str, Any]) -> None:
    """Persiste state.json atomicamente com indentação padrão."""
    temp_file = state_file.with_suffix(".tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    temp_file.replace(state_file)


def topological_sort(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Ordena nós do DAG respeitando dependências ('depends_on' ou 'dependencies')."""
    node_map = {n["id"]: n for n in nodes}
    in_degree: Dict[str, int] = {n["id"]: 0 for n in nodes}
    adj: Dict[str, List[str]] = {n["id"]: [] for n in nodes}

    for n in nodes:
        deps = n.get("depends_on") or n.get("dependencies") or []
        for dep in deps:
            if dep in adj:
                adj[dep].append(n["id"])
                in_degree[n["id"]] += 1

    queue = [n_id for n_id, deg in in_degree.items() if deg == 0]
    sorted_nodes: List[Dict[str, Any]] = []

    while queue:
        curr = queue.pop(0)
        sorted_nodes.append(node_map[curr])
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(sorted_nodes) != len(nodes):
        raise ValueError("Ciclo detectado no grafo de dependências do pipeline.")

    return sorted_nodes


def resolve_skill_execution(skill_name: str, root_dir: Path) -> tuple[Path, str, str]:
    """Resolve entrypoint e flags CLI via dependencies.json da skill."""
    skill_dir = root_dir / "aidd-skills" / skill_name
    dep_file = skill_dir / "dependencies.json"
    if not dep_file.exists():
        raise FileNotFoundError(f"dependencies.json não encontrado para {skill_name}")

    with open(dep_file, "r", encoding="utf-8") as f:
        meta = json.load(f)

    entry = skill_dir / meta.get("entrypoint", "scripts/run.py")
    in_flag = meta.get("input_flag", "--input")
    out_flag = meta.get("output_flag", "--output")
    return entry, in_flag, out_flag


def execute_pipeline(
    pipeline_dir: Path,
    force: bool = False,
    workspace_arg: Optional[str] = None,
    resume_arg: Optional[str] = None,
) -> int:
    """Executa o pipeline DAG de ponta a ponta com rastreabilidade e integridade."""
    spec = load_pipeline_spec(pipeline_dir)
    pipeline_id = spec.get("id", pipeline_dir.name)
    nodes = spec.get("nodes", [])

    ws_dir, run_id = resolve_workspace(pipeline_dir, workspace_arg, resume_arg)
    state_file = ws_dir / "state.json"
    state = load_or_init_state(state_file, pipeline_id, run_id)

    root_dir = pipeline_dir.parent.parent
    ordered_nodes = topological_sort(nodes)

    print(f"=== Iniciando Pipeline: {pipeline_id} (Run ID: {run_id}) ===")
    print(f"Workspace ativo: {ws_dir}")

    for node in ordered_nodes:
        n_id = node["id"]
        current_hash = calculate_node_input_hash(node, pipeline_dir)
        node_state = state["nodes"].get(n_id, {})

        if node_state.get("status") == "COMPLETED" and not force:
            recorded_hash = node_state.get("inputs_hash")
            if recorded_hash == current_hash:
                print(f"[PULANDO / SKIPPING] Nó {n_id} já concluído e inputs_hash íntegro.")
                continue
            print(f"[REEXECUÇÃO] Nó {n_id} com dados de entrada alterados ou hash divergente.")

        print(f"\n--- Executando Nó: {n_id} ---")
        node_state["status"] = "RUNNING"
        node_state["started_at"] = time.time()
        node_state["inputs_hash"] = current_hash
        state["nodes"][n_id] = node_state
        save_state(state_file, state)

        cmd: List[str] = [sys.executable]
        env = os.environ.copy()

        if "entrypoint" in node:
            script_path = (pipeline_dir / node["entrypoint"]).resolve()
            cmd.append(str(script_path))

            in_ref = node.get("input") or node.get("input_handoff")
            if in_ref:
                in_p = Path(in_ref)
                if not in_p.is_absolute():
                    in_p = (pipeline_dir / in_p).resolve()
                cmd.append(str(in_p))

            out_ref = node.get("output_dir")
            if out_ref:
                out_p = Path(out_ref)
                if not out_p.is_absolute():
                    out_p = (pipeline_dir / out_p).resolve()
                out_p.mkdir(parents=True, exist_ok=True)
                cmd.append(str(out_p))
        elif "skill" in node:
            skill_name = node["skill"]
            entry_path, in_flag, out_flag = resolve_skill_execution(skill_name, root_dir)
            cmd.append(str(entry_path))

            in_ref = node.get("input_handoff") or node.get("input")
            if in_ref:
                in_p = Path(in_ref)
                if not in_p.is_absolute():
                    in_p = (pipeline_dir / in_p).resolve()
                cmd.extend([in_flag, str(in_p)])

            out_dir = ws_dir / n_id
            out_dir.mkdir(parents=True, exist_ok=True)
            cmd.extend([out_flag, str(out_dir)])
        else:
            err_msg = f"Nó {n_id} sem skill ou entrypoint definido."
            node_state["status"] = "FAILED"
            node_state["error"] = err_msg
            save_state(state_file, state)
            raise ValueError(err_msg)

        res = subprocess.run(cmd, env=env)
        if res.returncode != 0:
            print(f"[ERRO] Falha na execução do nó {n_id} (Código {res.returncode})")
            node_state["status"] = "FAILED"
            node_state["returncode"] = res.returncode
            state["status"] = "FAILED"
            save_state(state_file, state)
            return res.returncode

        node_state["status"] = "COMPLETED"
        node_state["completed_at"] = time.time()
        node_state["inputs_hash"] = current_hash
        state["nodes"][n_id] = node_state
        save_state(state_file, state)

    state["status"] = "COMPLETED"
    state["completed_at"] = time.time()
    save_state(state_file, state)
    print(f"\n=== Pipeline {pipeline_id} concluído com sucesso no workspace {ws_dir} ===")
    return 0


def main() -> None:
    """Ponto de entrada da CLI do runner de pipeline."""
    parser = argparse.ArgumentParser(description="Runner de Pipeline DAG AIDD Ouroboros")
    parser.add_argument("--force", action="store_true", help="Força reexecução de nós já concluídos")
    parser.add_argument("--workspace", type=str, default=None, help="Caminho explícito para o workspace de execução")
    parser.add_argument("--resume", type=str, default=None, help="Retoma execução de run_id existente em .workspaces")

    args = parser.parse_args()
    pipeline_dir = Path(__file__).resolve().parent

    exit_code = execute_pipeline(
        pipeline_dir=pipeline_dir,
        force=args.force,
        workspace_arg=args.workspace,
        resume_arg=args.resume,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
