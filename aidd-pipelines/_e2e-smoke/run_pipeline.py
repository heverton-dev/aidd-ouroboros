"""Runner para o pipeline E2E Smoke (aidd-pipelines/_e2e-smoke).

Conecta de forma determinística e real:
- node-01-router (aidd-rea-router)
- node-02-app (aidd-rea-app-android)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from motores.governanca.handoff_crypto import selar_handoff


def run_pipeline(workspace_dir: Path) -> int:
    """Executa o pipeline E2E Smoke dentro do diretório de workspace fornecido."""
    workspace_dir.mkdir(parents=True, exist_ok=True)
    chave = os.getenv("AIDD_HANDOFF_KEY", "test")
    root_dir = Path(__file__).resolve().parent.parent.parent

    # Carrega PIPELINE.json
    pipeline_json_path = Path(__file__).resolve().parent / "PIPELINE.json"
    if not pipeline_json_path.exists():
        sys.stderr.write(f"PIPELINE.json nao encontrado em {pipeline_json_path}\n")
        return 1

    with open(pipeline_json_path, "r", encoding="utf-8") as f:
        pipeline_def = json.load(f)

    # 1. Executa node-01-router
    node1_dir = workspace_dir / "node-01-router"
    node1_dir.mkdir(parents=True, exist_ok=True)
    fixture_apk = root_dir / "tests" / "fixtures" / "sample_app.apk"
    if not fixture_apk.exists():
        sys.stderr.write(f"Fixture APK nao encontrada em {fixture_apk}\n")
        return 1

    # Invocação direta da classificação do router
    router_script = root_dir / "aidd-skills" / "aidd-rea-router" / "scripts" / "rea_router.py"
    cmd_router = [
        sys.executable,
        str(router_script),
        "--classify",
        str(fixture_apk),
    ]
    proc_router = subprocess.run(cmd_router, capture_output=True, text=True, check=False)
    if proc_router.returncode != 0:
        sys.stderr.write(f"Falha no router: {proc_router.stderr}\n")
        return 1

    router_output = json.loads(proc_router.stdout.strip())
    node1_handoff_path = node1_dir / "handoff.json"

    body_node1 = {
        "source_step": "node-01-router",
        "target_step": "node-02-app",
        "domain_data": {
            "target_path": str(fixture_apk),
            "classification": router_output,
        },
        "artifacts": [
            {
                "path": str(fixture_apk),
                "descricao": "Fixture APK real",
            }
        ],
    }

    selar_handoff(body_node1, chave=chave, destino=node1_handoff_path)

    # 2. Executa node-02-app
    node2_dir = workspace_dir / "node-02-app"
    node2_dir.mkdir(parents=True, exist_ok=True)
    node2_handoff_path = node2_dir / "handoff.json"

    app_script = root_dir / "aidd-skills" / "aidd-rea-app-android" / "scripts" / "app_reengineer.py"
    cmd_app = [
        sys.executable,
        str(app_script),
        "--input",
        str(fixture_apk),
        "--output-dir",
        str(node2_dir),
        "--output-handoff",
        str(node2_handoff_path),
    ]
    proc_app = subprocess.run(cmd_app, capture_output=True, text=True, check=False)
    if proc_app.returncode != 0:
        sys.stderr.write(f"Falha no app_reengineer: {proc_app.stderr}\n")
        return 1

    # O app_reengineer gera o handoff sem selagem criptográfica por padrão se a chave não foi repassada pelo CLI dele;
    # Garantimos que o handoff final em node2_handoff_path esteja selado com selar_handoff
    if node2_handoff_path.exists():
        with open(node2_handoff_path, "r", encoding="utf-8") as f:
            raw_node2_data = json.load(f)
        # Se for envelope já selado, mantemos ou reselamos com a chave
        body_node2 = raw_node2_data.get("body", raw_node2_data)
        selar_handoff(body_node2, chave=chave, destino=node2_handoff_path)

    # 3. Emite state.json
    state_data = {
        "pipeline_id": pipeline_def.get("pipeline_id", "pipeline-e2e-smoke"),
        "status": "COMPLETED",
        "nodes": {
            "node-01-router": {"status": "SUCCESS", "handoff": str(node1_handoff_path)},
            "node-02-app": {"status": "SUCCESS", "handoff": str(node2_handoff_path)},
        },
    }
    with open(workspace_dir / "state.json", "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2, ensure_ascii=False)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Runner do pipeline E2E Smoke.")
    parser.add_argument("--workspace", required=True, type=Path, help="Diretório de workspace")
    args = parser.parse_args()
    return run_pipeline(args.workspace)


if __name__ == "__main__":
    sys.exit(main())
