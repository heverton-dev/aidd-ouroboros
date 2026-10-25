# -*- coding: utf-8 -*-
"""Testes de seguranca para sync_all.ps1 e scripts sync individuais (NT-02)."""
import json
import shutil
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC_ALL_PS1 = REPO_ROOT / "aidd-skills" / "sync_all.ps1"


def run_powershell(args, cwd=None):
    """Executa comando powershell de forma segura."""
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass"] + args
    result = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result


def test_sync_all_error_action_preference_is_stop():
    """sync_all.ps1 deve configurar ErrorActionPreference = Stop e nao SilentlyContinue."""
    content = SYNC_ALL_PS1.read_text(encoding="utf-8")
    assert 'SilentlyContinue' not in content, "sync_all.ps1 nao deve usar SilentlyContinue"
    assert '$ErrorActionPreference = "Stop"' in content, "sync_all.ps1 deve definir ErrorActionPreference = 'Stop'"


def test_sync_all_accepts_harness_root_parameter():
    """sync_all.ps1 deve aceitar param([string]$HarnessRoot, [switch]$WhatIf, [switch]$DryRun, [switch]$Force)."""
    content = SYNC_ALL_PS1.read_text(encoding="utf-8")
    assert "param(" in content, "sync_all.ps1 deve declarar bloco param"
    assert "$HarnessRoot" in content, "sync_all.ps1 deve declarar parametro $HarnessRoot"
    assert "$DryRun" in content, "sync_all.ps1 deve declarar parametro $DryRun"


def test_sync_all_preserves_legacy_folder_without_marker(tmp_path):
    """Pastas legadas sem marcador .aidd-managed NAO podem ser removidas."""
    harness_root = tmp_path / "mock_harness"
    legacy_dir = harness_root / ".agents" / "skills" / "aidd-video-reengineer"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    user_file = legacy_dir / "user_important_code.py"
    user_file.write_text("# Arquivo do usuario", encoding="utf-8")

    res = run_powershell([
        "-File", str(SYNC_ALL_PS1),
        "-HarnessRoot", str(harness_root)
    ])

    assert legacy_dir.exists(), "Pasta legada sem marcador .aidd-managed foi removida indevidamente!"
    assert user_file.exists(), "Arquivo de usuario dentro de legado nao-gerenciado foi apagado!"


def test_sync_all_removes_legacy_folder_with_marker(tmp_path):
    """Pastas legadas COM marcador .aidd-managed devem ser removidas com seguranca."""
    harness_root = tmp_path / "mock_harness"
    legacy_dir = harness_root / ".agents" / "skills" / "aidd-video-reengineer"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    marker = legacy_dir / ".aidd-managed"
    marker.write_text(json.dumps({
        "name": "aidd-video-reengineer",
        "managed_by": "aidd-ouroboros",
        "version": "1.0.0"
    }), encoding="utf-8")

    res = run_powershell([
        "-File", str(SYNC_ALL_PS1),
        "-HarnessRoot", str(harness_root)
    ])

    assert not legacy_dir.exists(), "Pasta legada gerenciada deveria ter sido removida."


def test_sync_all_dry_run_does_not_modify(tmp_path):
    """DryRun / WhatIf nao deve remover pastas gerenciadas nem criar novas."""
    harness_root = tmp_path / "mock_harness"
    legacy_dir = harness_root / ".agents" / "skills" / "aidd-video-reengineer"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    marker = legacy_dir / ".aidd-managed"
    marker.write_text(json.dumps({
        "name": "aidd-video-reengineer",
        "managed_by": "aidd-ouroboros",
        "version": "1.0.0"
    }), encoding="utf-8")

    res = run_powershell([
        "-File", str(SYNC_ALL_PS1),
        "-HarnessRoot", str(harness_root),
        "-DryRun"
    ])

    assert legacy_dir.exists(), "DryRun nao deve remover pastas."


def test_sync_skill_creates_managed_marker(tmp_path):
    """Cada sync.ps1 deve receber -HarnessRoot e criar o marcador .aidd-managed."""
    harness_root = tmp_path / "mock_harness"
    craft_sync = REPO_ROOT / "aidd-skills" / "aidd-craft-story-ptbr" / "sync.ps1"
    
    res = run_powershell([
        "-File", str(craft_sync),
        "-HarnessRoot", str(harness_root)
    ])

    dest_skill = harness_root / ".agents" / "skills" / "aidd-craft-story-ptbr"
    assert dest_skill.exists(), "Destino da skill deveria ter sido criado."
    marker = dest_skill / ".aidd-managed"
    assert marker.exists(), "Marcador .aidd-managed nao foi gerado no destino."
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data.get("managed_by") == "aidd-ouroboros"
    assert data.get("name") == "aidd-craft-story-ptbr"
