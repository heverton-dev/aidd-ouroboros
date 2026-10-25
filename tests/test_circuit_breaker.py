#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_circuit_breaker.py — Suíte de Testes Automatizados para o Circuit Breaker de Governança
Padrão: AIDD Universal Architecture / Zero Stubs / Zero Mocks / HMAC-SHA256
"""

from __future__ import annotations

from pathlib import Path
import sys

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pytest

from motores.governanca.gate_factory_completeness import (
    auditar_completude_skills,
    auditar_completude_pipelines,
    executar_circuit_breaker,
)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_circuit_breaker_detects_incomplete_structures(repo_root: Path):
    """Garante que o Circuit Breaker analisa a anatomia e retorna tupla booleana e lista de erros."""
    ok, erros = executar_circuit_breaker(repo_root)
    assert isinstance(ok, bool)
    assert isinstance(erros, list)


def test_circuit_breaker_fails_on_empty_dir(tmp_path: Path):
    """Garante que pastas criadas ad-hoc sem arquivos obrigatórios desarmam o circuit breaker."""
    fake_skills = tmp_path / "aidd-skills"
    fake_skills.mkdir()
    adhoc_skill = fake_skills / "aidd-fake-adhoc"
    adhoc_skill.mkdir()
    # Cria apenas SKILL.md sem templates, references, sync.ps1, etc.
    (adhoc_skill / "SKILL.md").write_text("---\nname: fake\ndescription: fake\n---\n", encoding="utf-8")

    ok, erros = auditar_completude_skills(tmp_path)
    assert not ok, "Skill ad-hoc deve ser reprovada pelo Circuit Breaker"
    assert any("[SKILL ANÊMICA]" in e for e in erros)
