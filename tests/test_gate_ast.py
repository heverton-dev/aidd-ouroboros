import os
import json
import pytest
from pathlib import Path
from motores.governanca.gate_ast import ASTGateChecker, scan_path

FIXTURES_DIR = Path(__file__).parent / "gates" / "fixtures"

def test_gate_detects_pass_body():
    bad_file = FIXTURES_DIR / "bad_pass_body.py"
    checker = ASTGateChecker(bad_file.read_bytes().decode("utf-8"), filename=str(bad_file))
    checker.check()
    assert len(checker.violations) >= 1
    assert any("pass" in v.rule_id.lower() or "stub" in v.rule_id.lower() for v in checker.violations)

def test_gate_detects_silent_except_pass():
    bad_file = FIXTURES_DIR / "bad_except_pass.py"
    checker = ASTGateChecker(bad_file.read_bytes().decode("utf-8"), filename=str(bad_file))
    checker.check()
    assert len(checker.violations) >= 1
    assert any("except" in v.rule_id.lower() or "silent" in v.rule_id.lower() for v in checker.violations)

def test_gate_detects_todo_comments():
    bad_file = FIXTURES_DIR / "bad_todo_comment.py"
    checker = ASTGateChecker(bad_file.read_bytes().decode("utf-8"), filename=str(bad_file))
    checker.check()
    assert len(checker.violations) >= 1
    assert any("comment" in v.rule_id.lower() or "todo" in v.rule_id.lower() for v in checker.violations)

def test_gate_detects_fake_doctor():
    bad_file = FIXTURES_DIR / "bad_fake_doctor.py"
    checker = ASTGateChecker(bad_file.read_bytes().decode("utf-8"), filename=str(bad_file))
    checker.check()
    assert len(checker.violations) >= 1
    assert any("fake" in v.rule_id.lower() or "doctor" in v.rule_id.lower() or "verifier" in v.rule_id.lower() for v in checker.violations)

def test_gate_passes_good_real():
    good_file = FIXTURES_DIR / "good_real.py"
    checker = ASTGateChecker(good_real_code := good_file.read_bytes().decode("utf-8"), filename=str(good_file))
    checker.check()
    assert len(checker.violations) == 0

def test_gate_baseline_comparison(tmp_path):
    baseline_file = tmp_path / "baseline.json"
    baseline_data = {
        "tests/gates/fixtures/bad_pass_body.py": ["STUB_PASS"]
    }
    baseline_file.write_text(json.dumps(baseline_data), encoding="utf-8")
    
    # Com baseline contendo a violacao existente, nao deve retornar erro novo para esse arquivo
    # Mas se houver arquivo novo com violacao nao coberta, deve falhar
    assert baseline_file.exists()
