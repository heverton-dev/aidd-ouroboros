# -*- coding: utf-8 -*-
"""Testes da skill mestra aidd-ouroboros-master."""
from pathlib import Path
import json
import subprocess
import sys

SKILL_HOME = Path(__file__).resolve().parent.parent
REPO_ROOT = SKILL_HOME.parent.parent
SCRIPT = SKILL_HOME / "scripts" / "ouroboros_master.py"


def test_gate_ast_zero_stubs():
    sys.path.insert(0, str(REPO_ROOT))
    from motores.governanca.gate_ast import scan_path

    result = scan_path(SKILL_HOME)
    assert result.passed, "Gate AST falhou: " + ", ".join(getattr(result, "errors", []) or [])


def test_doctor_and_schema_paths():
    assert SCRIPT.is_file()
    assert (REPO_ROOT / "schemas" / "SPEC_PIPELINE.schema.json").is_file()


def test_init_spec_rejects_placeholder_orchestrate(tmp_path):
    spec_path = tmp_path / "SPEC_PIPELINE.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--from-nl",
            "teste de semeadura",
            "--output-spec",
            str(spec_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert proc.returncode == 0
    assert spec_path.is_file()
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    assert data["approved"] is False
    assert data["user_request"] == "teste de semeadura"

    proc2 = subprocess.run(
        [sys.executable, str(SCRIPT), "--orchestrate", str(spec_path), "--output-dir", str(tmp_path / "out")],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert proc2.returncode == 2
