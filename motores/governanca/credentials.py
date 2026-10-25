#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
credentials.py — Carregador Determinístico de Credenciais e Ambiente para o Ouroboros
Padrão: AIDD Universal Architecture / Zero Stubs / Zero Mocks / HMAC-SHA256
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional


def carregar_env_local(caminho_env: Optional[Path | str] = None) -> Dict[str, str]:
    """Lê arquivo .env local e popula variáveis em os.environ se não estiverem definidas."""
    if caminho_env is None:
        raiz = Path(__file__).resolve().parent.parent.parent
        alvo = raiz / ".env"
    else:
        alvo = Path(caminho_env)

    variaveis: Dict[str, str] = {}
    if not alvo.is_file():
        return variaveis

    linhas = alvo.read_text(encoding="utf-8").splitlines()
    for linha in linhas:
        l = linha.strip()
        if not l or l.startswith("#") or "=" not in l:
            continue
        chave, _, valor = l.partition("=")
        chave = chave.strip()
        valor = valor.strip().strip("'\"")
        variaveis[chave] = valor
        if chave not in os.environ:
            os.environ[chave] = valor

    return variaveis


def obter_credenciais_ia() -> Dict[str, Optional[str]]:
    """Recupera status e valores de credenciais para Gemini e Google Flow."""
    carregar_env_local()
    return {
        "execution_mode": os.getenv("OUROBOROS_EXECUTION_MODE", "DRY_RUN").upper(),
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        "gcp_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "gcp_location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "gcp_credentials": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    }


def verificar_prontidao_live() -> tuple[bool, list[str]]:
    """Valida se o ambiente possui as credenciais necessárias para LIVE RUN."""
    creds = obter_credenciais_ia()
    ausentes: list[str] = []

    if not creds["gemini_api_key"] or creds["gemini_api_key"] == "sua_chave_gemini_aqui":
        ausentes.append("GEMINI_API_KEY")

    if not creds["gcp_project"] or creds["gcp_project"] == "seu-projeto-gcp-id":
        ausentes.append("GOOGLE_CLOUD_PROJECT")

    pronto = len(ausentes) == 0
    return pronto, ausentes
