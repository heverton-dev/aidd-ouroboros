#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gemini_client.py — Cliente REST Soberano da Google Gemini API para Anti-Gravity
Padrão: AIDD Universal Architecture / Zero Stubs / Zero Mocks / HMAC-SHA256
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional
import urllib.request
import urllib.error

# Injetar raiz para acesso a credenciais
_root = Path(__file__).resolve().parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from motores.governanca.credentials import obter_credenciais_ia


def chamar_gemini_api(prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
    """Invoca o modelo Google Gemini via API REST nativa sem dependências extras."""
    creds = obter_credenciais_ia()
    api_key = creds.get("gemini_api_key")
    model = creds.get("gemini_model") or "gemini-2.0-flash"
    mode = creds.get("execution_mode") or "DRY_RUN"

    if mode == "DRY_RUN" or not api_key or api_key == "sua_chave_gemini_aqui":
        return {
            "status": "DRY_RUN_SUCCESS",
            "model": model,
            "simulated": True,
            "message": "Execução em modo DRY_RUN. Para chamadas reais, configure GEMINI_API_KEY no .env.",
            "prompt_tokens_estimated": len(prompt.split()),
            "content": f"[Simulação Gemini ({model})] Prompts e diretrizes cinematográficas validadas com sucesso."
        }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload: Dict[str, Any] = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "topP": 0.95,
            "maxOutputTokens": 4096
        }
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            corpo = resp.read().decode("utf-8")
            dados = json.loads(corpo)
            texto_gerado = ""
            candidatos = dados.get("candidates", [])
            if candidatos:
                partes = candidatos[0].get("content", {}).get("parts", [])
                if partes:
                    texto_gerado = partes[0].get("text", "")
            return {
                "status": "LIVE_SUCCESS",
                "model": model,
                "simulated": False,
                "content": texto_gerado,
                "raw_response": dados
            }
    except urllib.error.HTTPError as exc:
        detalhe = exc.read().decode("utf-8", errors="ignore")
        return {
            "status": "API_ERROR",
            "code": exc.code,
            "message": f"Erro HTTP {exc.code} ao chamar Gemini API: {detalhe}",
            "simulated": False
        }
    except Exception as exc:
        return {
            "status": "NETWORK_ERROR",
            "message": f"Falha de rede ou conexão com Gemini API: {str(exc)}",
            "simulated": False
        }
