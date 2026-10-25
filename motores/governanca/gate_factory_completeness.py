#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gate_factory_completeness.py — Quality Gate e Circuit Breaker de Anatomia Enterprise
Padrão: AIDD Universal Architecture / Zero Stubs / Zero Mocks / HMAC-SHA256

Fiscaliza se todas as skills e pipelines possuem a estrutura canônica completa
produzida pela meta-fábrica, desarmando o processo se houver criação ad-hoc ou anêmica.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

SKILL_OBLIGATORY_FILES = [
    "SKILL.md",
    "AGENTS.md",
    "RULES.md",
    "dependencies.json",
    "LICENSE",
    "sync.ps1",
    "sync.sh",
]

SKILL_OBLIGATORY_DIRS = [
    "references",
    "templates",
    "scripts",
]

PIPELINE_OBLIGATORY_FILES = [
    "PIPELINE.json",
    "AGENTS.md",
    "RULES.md",
    "dependencies.json",
    "LICENSE",
    "run_pipeline.py",
    "state.json",
]

PIPELINE_OBLIGATORY_DIRS = [
    "context",
    "context/input",
    "context/handoffs",
    "context/output",
]


def auditar_completude_skills(root: Path) -> Tuple[bool, List[str]]:
    skills_dir = root / "aidd-skills"
    if not skills_dir.is_dir():
        return False, ["Diretório aidd-skills/ não encontrado."]

    violacoes: List[str] = []
    pastas_skills = [p for p in skills_dir.glob("*") if p.is_dir() and not p.name.startswith(".")]

    for sk in pastas_skills:
        for f in SKILL_OBLIGATORY_FILES:
            alvo = sk / f
            if not alvo.is_file():
                violacoes.append(f"[SKILL ANÊMICA] {sk.name}: arquivo obrigatório ausente -> {f}")

        for d in SKILL_OBLIGATORY_DIRS:
            alvo_d = sk / d
            if not alvo_d.is_dir():
                violacoes.append(f"[SKILL ANÊMICA] {sk.name}: pasta estrutural ausente -> {d}")
            else:
                conteudo = list(alvo_d.glob("*"))
                if not conteudo:
                    violacoes.append(f"[SKILL ANÊMICA] {sk.name}: pasta {d}/ está vazia")

    return len(violacoes) == 0, violacoes


def auditar_completude_pipelines(root: Path) -> Tuple[bool, List[str]]:
    pipe_dir = root / "aidd-pipelines"
    if not pipe_dir.is_dir():
        return False, ["Diretório aidd-pipelines/ não encontrado."]

    violacoes: List[str] = []
    pastas_pipes = [p for p in pipe_dir.glob("*") if p.is_dir() and not p.name.startswith(".")]

    for pipe in pastas_pipes:
        for f in PIPELINE_OBLIGATORY_FILES:
            alvo = pipe / f
            if not alvo.is_file():
                violacoes.append(f"[PIPELINE INCOMPLETO] {pipe.name}: arquivo obrigatório ausente -> {f}")

        for d in PIPELINE_OBLIGATORY_DIRS:
            alvo_d = pipe / d
            if not alvo_d.is_dir():
                violacoes.append(f"[PIPELINE INCOMPLETO] {pipe.name}: pasta estrutural ausente -> {d}")

    return len(violacoes) == 0, violacoes


def executar_circuit_breaker(root: Path) -> Tuple[bool, List[str]]:
    """Executa a verificação combinada. Retorna (True, []) ou (False, erros)."""
    ok_sk, erros_sk = auditar_completude_skills(root)
    ok_pipe, erros_pipe = auditar_completude_pipelines(root)

    todos_erros = erros_sk + erros_pipe
    return (ok_sk and ok_pipe), todos_erros
