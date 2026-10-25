"""
Testes unitários para motores/governanca/dependency_resolver.py (NT-14).
Cobre:
- Checagem (--check) com itens ausentes (exit 1) e itens presentes (exit 0).
- Não vazamento de valores de variáveis de ambiente no stdout/stderr/json.
- Instalação (--install) sem flag --yes deve falhar (exit 1).
- Instalação (--install) com versões despinadas/não fixadas deve falhar (exit 1).
- Mock de subprocesso em instalação para proteger host real.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from motores.governanca.dependency_resolver import (
    DependencyResolver,
    main,
)


@pytest.fixture
def sample_manifest(tmp_path: Path) -> Path:
    data = {
        "name": "test-module",
        "version": "1.0.0",
        "system_binaries": [
            {"name": "git", "required": True},
            {"name": "non_existent_binary_xyz_123", "required": True},
        ],
        "python_packages": [
            "pytest==8.0.0",
        ],
        "env_vars": [
            "SECRET_API_TOKEN_FOR_TEST",
            "MISSING_ENV_VAR_ABC",
        ],
        "core_skills": [
            "aidd-rea-router",
        ],
    }
    manifest_file = tmp_path / "dependencies.json"
    manifest_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return manifest_file


@pytest.fixture
def valid_manifest(tmp_path: Path) -> Path:
    data = {
        "name": "test-valid-module",
        "version": "1.0.0",
        "system_binaries": [
            {"name": "python", "required": True},
        ],
        "python_packages": [
            "pytest>=7.0.0",
        ],
        "env_vars": [
            "TEST_EXISTING_ENV_VAR",
        ],
        "core_skills": [],
    }
    manifest_file = tmp_path / "dependencies.json"
    manifest_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return manifest_file


def test_check_missing_dependencies_returns_exit_1(sample_manifest: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("SECRET_API_TOKEN_FOR_TEST", "SUPER_CONFIDENTIAL_VALUE_999")
    ret = main(["--manifest", str(sample_manifest), "--check"])
    assert ret == 1
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["ok"] is False
    assert "system_binaries" in report["results"]
    binaries = {item["name"]: item["status"] for item in report["results"]["system_binaries"]}
    assert binaries["non_existent_binary_xyz_123"] == "MISSING"


def test_env_var_values_never_leak_in_output(sample_manifest: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    secret_value = "SECRET_TOKEN_DO_NOT_LEAK_ME_7777777"
    monkeypatch.setenv("SECRET_API_TOKEN_FOR_TEST", secret_value)
    
    main(["--manifest", str(sample_manifest), "--check"])
    captured = capsys.readouterr()
    
    assert secret_value not in captured.out
    assert secret_value not in captured.err
    
    report = json.loads(captured.out)
    env_results = report["results"]["env_vars"]
    for item in env_results:
        assert "value" not in item
        assert secret_value not in str(item)


def test_check_ready_dependencies_returns_exit_0(valid_manifest: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("TEST_EXISTING_ENV_VAR", "exists")
    ret = main(["--manifest", str(valid_manifest), "--check"])
    assert ret == 0
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert report["ok"] is True


def test_install_without_yes_flag_fails(sample_manifest: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ret = main(["--manifest", str(sample_manifest), "--install"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "--yes" in captured.err or "--yes" in captured.out


def test_install_with_unpinned_versions_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest_data = {
        "name": "unpinned-test",
        "python_packages": [
            "requests>=2.28.0",
        ],
    }
    manifest_file = tmp_path / "dependencies.json"
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
    
    ret = main(["--manifest", str(manifest_file), "--install", "--yes"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "pinned" in captured.err.lower() or "pinned" in captured.out.lower() or "unpinned" in captured.err.lower()


def test_install_pinned_packages_executes_safely(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_data = {
        "name": "pinned-test",
        "python_packages": [
            "black==24.3.0",
        ],
    }
    manifest_file = tmp_path / "dependencies.json"
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
    
    mock_run = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=0))
    monkeypatch.setattr(subprocess, "run", mock_run)
    
    ret = main(["--manifest", str(manifest_file), "--install", "--yes"])
    assert ret == 0
    assert mock_run.called
    cmd_args = mock_run.call_args[0][0]
    assert "black==24.3.0" in cmd_args


def test_resolver_accepts_directory_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_data = {
        "name": "dir-test",
        "python_packages": [],
    }
    manifest_file = tmp_path / "dependencies.json"
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
    
    resolver = DependencyResolver(tmp_path)
    report = resolver.check()
    assert report["ok"] is True
