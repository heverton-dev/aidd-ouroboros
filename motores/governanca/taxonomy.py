"""
Módulo de resolução e validação de taxonomia de skills e pipelines (NT-04).
Garante determinismo, fail-closed para skills desconhecidas e compatibilidade com aliases legados.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any, Dict

# Localização canônica da taxonomia
REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent
TAXONOMY_PATH: Path = REPO_ROOT / "aidd-skills" / "TAXONOMY.json"


def load_taxonomy(path: Path | None = None) -> Dict[str, Any]:
    """Carrega a taxonomia oficial do AIDD a partir do disco."""
    target_path = path or TAXONOMY_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Arquivo de taxonomia não encontrado: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    return data


def resolve_skill_name(name: str, taxonomy_data: Dict[str, Any] | None = None) -> str:
    """
    Resolve o nome de uma skill para sua forma canônica.

    Regras:
    1. Se o nome constar em 'skills', retorna o próprio nome.
    2. Se constar em 'aliases', emite UserWarning e retorna o nome canônico.
    3. Se não constar em nenhum, lança ValueError (fail-closed).
    """
    tax = taxonomy_data or load_taxonomy()
    skills: Dict[str, Any] = tax.get("skills", {})
    aliases: Dict[str, str] = tax.get("aliases", {})

    if name in skills:
        return name

    if name in aliases:
        canonical = aliases[name]
        warnings.warn(
            f"Skill '{name}' é um alias legado. Use o nome canônico '{canonical}'.",
            UserWarning,
            stacklevel=2,
        )
        return canonical

    raise ValueError(f"Skill '{name}' não consta na taxonomia oficial.")
