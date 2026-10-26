import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from motores.governanca.handoff_crypto import verify_handoff


@pytest.mark.e2e
def test_pipeline_real_e2e_smoke(tmp_path):
    root_dir = Path(__file__).resolve().parent.parent.parent
    pipeline_dir = root_dir / "aidd-pipelines" / "_e2e-smoke"
    run_script = pipeline_dir / "run_pipeline.py"
    workspace_dir = tmp_path / "workspace"

    # Preparar variáveis de ambiente com chave HMAC exigida
    env = os.environ.copy()
    env["AIDD_HANDOFF_KEY"] = "test"
    env["PYTHONPATH"] = str(root_dir)

    # 1. Execução do runner do pipeline
    cmd = [
        sys.executable,
        str(run_script),
        "--workspace",
        str(workspace_dir),
    ]

    result = subprocess.run(cmd, env=env, cwd=str(root_dir), capture_output=True, text=True)

    # Asserção 1: Exit code 0
    assert result.returncode == 0, f"Runner falhou com código {result.returncode}. Output: {result.stdout} {result.stderr}"

    # Asserção 2: state.json no workspace com status COMPLETED
    state_file = workspace_dir / "state.json"
    assert state_file.exists(), f"state.json não foi gerado em {state_file}"
    state_data = json.loads(state_file.read_text(encoding="utf-8"))
    assert state_data.get("status") == "COMPLETED", f"Status esperado COMPLETED, obtido: {state_data.get('status')}"

    # Asserção 3: Handoffs selados com HMAC-SHA256 íntegro para cada nó
    node_01_handoff_path = workspace_dir / "node-01-router" / "handoff.json"
    node_02_handoff_path = workspace_dir / "node-02-app" / "handoff.json"

    assert node_01_handoff_path.exists(), f"Handoff node-01 não encontrado em {node_01_handoff_path}"
    assert node_02_handoff_path.exists(), f"Handoff node-02 não encontrado em {node_02_handoff_path}"

    with open(node_01_handoff_path, "r", encoding="utf-8") as f:
        node_01_payload = json.load(f)
    with open(node_02_handoff_path, "r", encoding="utf-8") as f:
        node_02_payload = json.load(f)

    assert verify_handoff(node_01_payload, "test") is True, "Handoff node-01 falhou na verificação HMAC-SHA256"
    assert verify_handoff(node_02_payload, "test") is True, "Handoff node-02 falhou na verificação HMAC-SHA256"

    # Asserção 4: metadados de domínio do nó 02 com permissões reais do fixture APK
    # Formato canônico HMAC usa domain_metadata; legado usava domain_data.
    body_02 = node_02_payload.get("body", {})
    domain_02 = body_02.get("domain_metadata") or body_02.get("domain_data") or {}
    permissions = domain_02.get("permissions", [])

    assert "android.permission.INTERNET" in permissions, "android.permission.INTERNET ausente no domain"
    assert "android.permission.ACCESS_FINE_LOCATION" in permissions, "android.permission.ACCESS_FINE_LOCATION ausente no domain"
    # Garantir que não há permissões inventadas / vazias
    assert all(isinstance(p, str) and p.startswith("android.permission.") for p in permissions), "Permissões contêm dados inválidos"
