"""Testes de integridade de resume e isolamento de workspace (NT-13).

Valida:
1. Isolamento por run_id em .workspaces/<run_id> ou --workspace customizado.
2. Armazenamento determinístico de inputs_hash no state.json de cada nó.
3. Resume com mesmo input pula nós concluídos.
4. Alteração no input força reexecução do nó.
5. Estado forjado (COMPLETED sem inputs_hash ou com hash inválido) não é pulado.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def test_workspace_isolation_and_inputs_hash_resume(tmp_path: Path) -> None:
    """Valida pipeline runner com workspace isolado e integridade de resume por hash."""
    pipeline_dir = tmp_path / "mock_pipeline"
    pipeline_dir.mkdir(parents=True)
    scripts_dir = pipeline_dir / "scripts"
    scripts_dir.mkdir()

    # Cria script mock determinístico de nó
    node_script = scripts_dir / "step.py"
    node_script.write_text(
        "import sys, json, pathlib\n"
        "input_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None\n"
        "out_dir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path('.')\n"
        "out_dir.mkdir(parents=True, exist_ok=True)\n"
        "counter_file = out_dir / 'exec_count.txt'\n"
        "count = int(counter_file.read_text()) if counter_file.exists() else 0\n"
        "counter_file.write_text(str(count + 1))\n"
        "out_file = out_dir / 'output.json'\n"
        "in_data = json.loads(input_path.read_text()) if input_path and input_path.exists() else {}\n"
        "out_file.write_text(json.dumps({'received': in_data, 'run': count + 1}))\n",
        encoding="utf-8",
    )

    # Cria input inicial
    input_file = pipeline_dir / "input.json"
    input_file.write_text(json.dumps({"payload": "initial_data"}), encoding="utf-8")

    # Copia o template de pipeline atualizado
    template_path = Path("aidd-skills/aidd-orchestrate-pipeline-creator/templates/RUN_PIPELINE_TEMPLATE.py")
    runner_code = template_path.read_text(encoding="utf-8")

    # Pipeline definition com 1 nó
    pipeline_json = pipeline_dir / "pipeline.json"
    pipeline_json.write_text(
        json.dumps({
            "pipeline_name": "test-resume",
            "version": "1.0.0",
            "nodes": [
                {
                    "id": "step_1",
                    "skill": "mock-step",
                    "entrypoint": "scripts/step.py",
                    "input_handoff": "input.json",
                    "output_dir": "outputs/step_1",
                    "dependencies": []
                }
            ]
        }),
        encoding="utf-8",
    )

    runner_file = pipeline_dir / "run_pipeline.py"
    runner_file.write_text(runner_code, encoding="utf-8")

    env = os.environ.copy()
    env["AIDD_HANDOFF_KEY"] = "test"

    # 1. Execução inicial sem --workspace: deve criar subpasta em .workspaces/
    res1 = subprocess.run(
        [sys.executable, str(runner_file)],
        cwd=str(pipeline_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    assert res1.returncode == 0, f"Falha execução 1: {res1.stderr}"

    workspaces_dir = pipeline_dir / ".workspaces"
    assert workspaces_dir.exists(), "Diretório .workspaces deve ser criado"
    runs = list(workspaces_dir.iterdir())
    assert len(runs) == 1, f"Deve existir exatamente 1 workspace criado, achou {runs}"
    run_dir = runs[0]
    run_id = run_dir.name

    state_file = run_dir / "state.json"
    assert state_file.exists(), "state.json deve residir no workspace do run"
    state = json.loads(state_file.read_text(encoding="utf-8"))

    # Verifica se inputs_hash foi gravado no nó
    node_state = state["nodes"]["step_1"]
    assert node_state["status"] == "COMPLETED"
    assert "inputs_hash" in node_state, "inputs_hash obrigatório em nó COMPLETED"
    orig_hash = node_state["inputs_hash"]
    assert orig_hash is not None and len(orig_hash) == 64

    # 2. Reexecuta com --resume <run_id> e mesma entrada -> nó deve ser pulado
    res2 = subprocess.run(
        [sys.executable, str(runner_file), "--resume", run_id],
        cwd=str(pipeline_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    assert res2.returncode == 0, f"Falha resume 1: {res2.stderr}"
    assert "PULANDO" in res2.stdout or "SKIPPING" in res2.stdout or "skipped" in res2.stdout.lower()

    # 3. Altera o input e reexecuta com --resume <run_id> -> hash muda, nó DEVE ser reexecutado
    input_file.write_text(json.dumps({"payload": "changed_data"}), encoding="utf-8")
    res3 = subprocess.run(
        [sys.executable, str(runner_file), "--resume", run_id],
        cwd=str(pipeline_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    assert res3.returncode == 0, f"Falha resume 2: {res3.stderr}"

    new_state = json.loads(state_file.read_text(encoding="utf-8"))
    new_hash = new_state["nodes"]["step_1"]["inputs_hash"]
    assert new_hash != orig_hash, "inputs_hash deve mudar quando a entrada mudar"

    # 4. Forja state.json com COMPLETED mas inputs_hash ausente/inválido -> nó NÃO deve ser pulado
    new_state["nodes"]["step_1"]["inputs_hash"] = "invalid_forged_hash"
    state_file.write_text(json.dumps(new_state), encoding="utf-8")

    res4 = subprocess.run(
        [sys.executable, str(runner_file), "--resume", run_id],
        cwd=str(pipeline_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    assert res4.returncode == 0
    refetched_state = json.loads(state_file.read_text(encoding="utf-8"))
    assert refetched_state["nodes"]["step_1"]["inputs_hash"] == new_hash, "Hash deve ser recalculado e restaurado"


def test_custom_workspace_flag(tmp_path: Path) -> None:
    """Valida uso da flag explícita --workspace <dir>."""
    pipeline_dir = tmp_path / "mock_pipeline_custom"
    pipeline_dir.mkdir(parents=True)
    scripts_dir = pipeline_dir / "scripts"
    scripts_dir.mkdir()

    node_script = scripts_dir / "step.py"
    node_script.write_text("print('ok')\n", encoding="utf-8")

    pipeline_json = pipeline_dir / "pipeline.json"
    pipeline_json.write_text(
        json.dumps({
            "pipeline_name": "test-custom-ws",
            "version": "1.0.0",
            "nodes": [
                {
                    "id": "step_1",
                    "skill": "mock-step",
                    "entrypoint": "scripts/step.py",
                    "dependencies": []
                }
            ]
        }),
        encoding="utf-8",
    )

    template_path = Path("aidd-skills/aidd-orchestrate-pipeline-creator/templates/RUN_PIPELINE_TEMPLATE.py")
    runner_file = pipeline_dir / "run_pipeline.py"
    runner_file.write_text(template_path.read_text(encoding="utf-8"), encoding="utf-8")

    custom_ws = tmp_path / "custom_workspace_target"
    env = os.environ.copy()
    env["AIDD_HANDOFF_KEY"] = "test"

    res = subprocess.run(
        [sys.executable, str(runner_file), "--workspace", str(custom_ws)],
        cwd=str(pipeline_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    assert res.returncode == 0, f"Falha custom workspace: {res.stderr}"
    assert (custom_ws / "state.json").exists(), "state.json deve ser criado no caminho informado em --workspace"
