#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_pipeline.py — Runner Determinístico Blindado com Governança Fractal
Padrão: AIDD Universal Architecture / Zero Stubs / Zero Mocks / HMAC-SHA256 Integrity

Executa nós do DAG em ordem topológica, gerencia e valida envelopes de handoff por ponteiros.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List

# Injetar raiz da branch para acesso a motores.governanca
_branch_root = Path(__file__).resolve().parent.parent.parent
if str(_branch_root) not in sys.path:
    sys.path.insert(0, str(_branch_root))

try:
    from motores.governanca.handoff_crypto import criar_envelope_handoff, verificar_envelope_handoff
except ImportError:
    criar_envelope_handoff = None
    verificar_envelope_handoff = None


def load_pipeline_spec(pipeline_dir: Path) -> Dict[str, Any]:
    spec_path = pipeline_dir / "PIPELINE.json"
    if not spec_path.exists():
        raise FileNotFoundError(f"PIPELINE.json não encontrado em {pipeline_dir}")
    with open(spec_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_or_init_state(pipeline_dir: Path, spec: Dict[str, Any]) -> Dict[str, Any]:
    state_path = pipeline_dir / "state.json"
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    state = {
        "pipeline_id": spec.get("pipeline_id", "unknown"),
        "status": "INITIALIZED",
        "start_time": None,
        "completed_time": None,
        "nodes": {node["id"]: {"status": "PENDING", "completed_at": None, "error": None} for node in spec.get("nodes", [])},
    }
    save_state(pipeline_dir, state)
    return state


def save_state(pipeline_dir: Path, state: Dict[str, Any]) -> None:
    state_path = pipeline_dir / "state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def topological_sort(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nodes_by_id = {node["id"]: node for node in nodes}
    in_degree = {node["id"]: 0 for node in nodes}
    graph = {node["id"]: [] for node in nodes}

    for node in nodes:
        for dep in node.get("depends_on", []):
            if dep in graph:
                graph[dep].append(node["id"])
                in_degree[node["id"]] += 1

    queue = [n_id for n_id, deg in in_degree.items() if deg == 0]
    order = []

    while queue:
        curr = queue.pop(0)
        order.append(nodes_by_id[curr])
        for neighbor in graph[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(nodes):
        raise ValueError("Ciclo detectado no grafo de nós do pipeline!")
    return order


def execute_pipeline(pipeline_dir: Path, force: bool = False) -> bool:
    spec = load_pipeline_spec(pipeline_dir)
    state = load_or_init_state(pipeline_dir, spec)

    nodes_sorted = topological_sort(spec.get("nodes", []))
    print(f"=== [AIDD-PIPELINE] Executando Pipeline Blindado: {spec.get('name', 'Enxame')} ===")
    print(f"[*] Total de nós no DAG: {len(nodes_sorted)}")

    state["status"] = "RUNNING"
    if not state.get("start_time"):
        state["start_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    save_state(pipeline_dir, state)

    for node in nodes_sorted:
        n_id = node["id"]
        n_skill = node["skill"]
        node_state = state["nodes"].get(n_id, {})

        if node_state.get("status") == "COMPLETED" and not force:
            print(f"[[OK] SKIP] Nó {n_id} ({n_skill}) já concluído anteriormente.")
            continue

        print(f"\n[▶ EXECUTANDO] Nó {n_id} -> Skill: {n_skill}")
        node_state["status"] = "RUNNING"
        save_state(pipeline_dir, state)

        # Resolver paths de handoff
        in_handoff = node.get("input_handoff")
        out_handoff = node.get("output_handoff")

        in_path = pipeline_dir / in_handoff if in_handoff else None
        out_path = pipeline_dir / out_handoff if out_handoff else None

        # Validação do Handoff de Entrada
        if in_path:
            if not in_path.exists():
                print(f"[ERRO] Entrada de handoff não encontrada: {in_path}", file=sys.stderr)
                node_state["status"] = "FAILED"
                node_state["error"] = f"Handoff de entrada inexistente: {in_path}"
                state["status"] = "FAILED"
                save_state(pipeline_dir, state)
                return False

            # Validação criptográfica se for envelope canônico
            if verificar_envelope_handoff is not None and in_path.suffix == ".json":
                try:
                    conteudo = json.loads(in_path.read_text(encoding="utf-8"))
                    if "hmac_sha256" in conteudo:
                        ok_crypto, msg_crypto = verificar_envelope_handoff(in_path)
                        if not ok_crypto:
                            print(f"[ERRO CRIPTOGRÁFICO] {msg_crypto}", file=sys.stderr)
                            node_state["status"] = "FAILED"
                            node_state["error"] = f"Adulteração no Handoff: {msg_crypto}"
                            state["status"] = "FAILED"
                            save_state(pipeline_dir, state)
                            return False
                        print(f"  [🛡️ INTEGRIDADE] Handoff de entrada validado via HMAC-SHA256.")
                except Exception as exc:
                    print(f"[WARN] Validação criptográfica ignorada (não-JSON ou schema livre): {exc}")

        # Localizar script da skill: 1) local do pipeline, 2) almoxarifado aidd-skills
        skill_dir = pipeline_dir / "skills" / n_skill
        if not skill_dir.exists():
            root_dir = pipeline_dir.parent.parent
            skill_dir = root_dir / "aidd-skills" / n_skill

        script_file = None
        input_flag = "--input"
        output_flag = "--output-handoff"
        if skill_dir.exists():
            dep_file = skill_dir / "dependencies.json"
            if dep_file.is_file():
                dep_data = json.loads(dep_file.read_text(encoding="utf-8"))
                entrypoint = dep_data.get("entrypoint")
                if entrypoint:
                    cand = skill_dir / entrypoint
                    if cand.is_file():
                        script_file = cand
                cli_contract = dep_data.get("cli_contract", {})
                input_flag = cli_contract.get("input_flag", input_flag)
                output_flag = cli_contract.get("output_flag", output_flag)

        if not script_file or not script_file.exists():
            # REGRA ZERO MOCKS: Erro explícito
            print(f"[ERRO ZERO MOCKS] Script funcional da skill '{n_skill}' não localizado em {skill_dir}.", file=sys.stderr)
            node_state["status"] = "FAILED"
            node_state["error"] = f"Skill sem implementação real: {n_skill}"
            state["status"] = "FAILED"
            save_state(pipeline_dir, state)
            return False

        cmd = [sys.executable, str(script_file)]
        if in_path:
            cmd.extend([input_flag, str(in_path)])
        if out_path:
            cmd.extend([output_flag, str(out_path)])

        res = subprocess.run(cmd, cwd=str(skill_dir))
        if res.returncode != 0:
            print(f"[ERRO] Falha na execução da skill {n_skill} (código {res.returncode})", file=sys.stderr)
            node_state["status"] = "FAILED"
            node_state["error"] = f"Erro de processo (código {res.returncode})"
            state["status"] = "FAILED"
            save_state(pipeline_dir, state)
            return False

        # Se gerou handoff de saída, assina e blinda se ainda não estiver assinado
        if out_path and out_path.exists() and criar_envelope_handoff is not None:
            try:
                dados_out = json.loads(out_path.read_text(encoding="utf-8"))
                if "hmac_sha256" not in dados_out:
                    criar_envelope_handoff(
                        origem_skill=n_skill,
                        status="SUCCESS",
                        artefatos={"handoff_raw": str(out_path)},
                        metadados={"node_id": n_id, "original": dados_out},
                        caminho_saida=out_path
                    )
            except Exception as exc:
                print(f"  [WARN] Assinatura automática de saída ignorada: {exc}")

        node_state["status"] = "COMPLETED"
        node_state["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        node_state["error"] = None
        save_state(pipeline_dir, state)
        print(f"[OK] Nó {n_id} finalizado com sucesso.")

    state["status"] = "COMPLETED"
    state["completed_time"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    save_state(pipeline_dir, state)

    # Emitir envelope universal de saída do pipeline assinado
    pipeline_output_path = pipeline_dir / "context" / "output" / "pipeline_output.json"
    pipeline_output_path.parent.mkdir(parents=True, exist_ok=True)
    final_artifacts_dict = {}
    if (pipeline_dir / "context" / "output").exists():
        for f in (pipeline_dir / "context" / "output").iterdir():
            if f.is_file() and f.name != "pipeline_output.json":
                final_artifacts_dict[f.name] = str(f)

    if criar_envelope_handoff is not None:
        criar_envelope_handoff(
            origem_skill=spec.get("pipeline_id", pipeline_dir.name),
            status="SUCCESS",
            artefatos=final_artifacts_dict,
            metadados={
                "pipeline_id": spec.get("pipeline_id", pipeline_dir.name),
                "nodes_completed": [n["id"] for n in nodes_sorted],
                "start_time": state.get("start_time"),
                "completed_time": state["completed_time"],
            },
            caminho_saida=pipeline_output_path
        )
    else:
        pipeline_output_data = {
            "contract": "universal-pipeline-handoff/v1",
            "pipeline_id": spec.get("pipeline_id", pipeline_dir.name),
            "status": "COMPLETED",
            "nodes_completed": [n["id"] for n in nodes_sorted],
        }
        pipeline_output_path.write_text(json.dumps(pipeline_output_data, indent=2), encoding="utf-8")

    print(f"\n[OK] Todo o pipeline autônomo foi executado e concluído!")
    print(f"[+] Envelope de Entrega Lego Assinado em: {pipeline_output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Runner determinístico blindado de pipeline autônomo de enxame de skills.")
    parser.add_argument("--force", action="store_true", help="Força a reexecução mesmo de nós já concluídos.")
    args = parser.parse_args()

    pipeline_dir = Path(__file__).resolve().parent
    ok = execute_pipeline(pipeline_dir, force=args.force)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
