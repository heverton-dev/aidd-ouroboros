"""Testes TDD para a robustez do audit_runner.py (NT-16)."""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path

from motores.governanca.handoff_crypto import selar_handoff, abrir


def test_print_root_padrao_executado_de_fora():
    """Testa --print-root executado a partir de um diretório temporário arbitrário."""
    repo_root = Path(__file__).resolve().parent.parent
    audit_runner_script = repo_root / "motores" / "governanca" / "audit_runner.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        res = subprocess.run(
            [sys.executable, str(audit_runner_script), "--print-root"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        output_path = Path(res.stdout.strip()).resolve()
        assert output_path == repo_root.resolve()


def test_print_root_customizado():
    """Testa --print-root quando a flag --root e informada explicitamente."""
    repo_root = Path(__file__).resolve().parent.parent
    audit_runner_script = repo_root / "motores" / "governanca" / "audit_runner.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        custom_root = Path(temp_dir).resolve()
        res = subprocess.run(
            [sys.executable, str(audit_runner_script), "--root", str(custom_root), "--print-root"],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        output_path = Path(res.stdout.strip()).resolve()
        assert output_path == custom_root


def test_banner_sem_string_proibida():
    """Garante que a execucao com --skip-pytest nao contenha a string legada proibida."""
    repo_root = Path(__file__).resolve().parent.parent
    audit_runner_script = repo_root / "motores" / "governanca" / "audit_runner.py"

    res = subprocess.run(
        [sys.executable, str(audit_runner_script), "--skip-pytest"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    # A string legada proibida
    assert "feature-matt-penny" not in res.stdout
    assert "feature-matt-penny" not in res.stderr
    assert "AUDITORIA DE QUALITY GATES FRACTAIS" in res.stdout


def test_workspace_valido_e_invalido():
    """Testa validacao de integridade de envelopes com --workspace."""
    repo_root = Path(__file__).resolve().parent.parent
    audit_runner_script = repo_root / "motores" / "governanca" / "audit_runner.py"

    with tempfile.TemporaryDirectory() as temp_dir:
        ws_path = Path(temp_dir)
        env_file = ws_path / "envelope_valido.json"
        selar_handoff({"tarefa": "nt-16", "status": "ok"}, chave="test-key", destino=env_file)

        # Executa com workspace valido
        res_ok = subprocess.run(
            [sys.executable, str(audit_runner_script), "--skip-pytest", "--skip-circuit-breaker", "--workspace", str(ws_path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        assert res_ok.returncode == 0
        assert "Workspace envelopes: OK" in res_ok.stdout

        # Corrompe o envelope
        with open(env_file, "r+", encoding="utf-8") as f:
            conteudo = json.load(f)
            conteudo["body"]["tarefa"] = "corrompido"
            f.seek(0)
            f.truncate()
            json.dump(conteudo, f)

        # Executa com envelope corrompido -> exit 1
        res_fail = subprocess.run(
            [sys.executable, str(audit_runner_script), "--skip-pytest", "--skip-circuit-breaker", "--workspace", str(ws_path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        assert res_fail.returncode == 1
        assert "FALHA" in res_fail.stdout or "FALHA" in res_fail.stderr


def test_auditar_workspace_unitario():
    """Testa diretamente a funcao auditar_workspace."""
    from motores.governanca.audit_runner import auditar_workspace

    with tempfile.TemporaryDirectory() as temp_dir:
        ws_path = Path(temp_dir)
        env_file = ws_path / "envelope_1.json"
        selar_handoff({"modulo": "teste", "sucesso": True}, chave="test-key", destino=env_file)

        ok, errs = auditar_workspace(ws_path)
        assert ok is True
        assert len(errs) == 0

        # Adiciona envelope inválido
        invalido_file = ws_path / "envelope_invalido.json"
        with open(invalido_file, "w", encoding="utf-8") as f:
            json.dump({"body": {"tarefa": "bad"}, "seal": {"hmac_sha256": "invalido"}}, f)

        ok_bad, errs_bad = auditar_workspace(ws_path)
        assert ok_bad is False
        assert len(errs_bad) == 1


