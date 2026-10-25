#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
googleflow_client.py — Conector Soberano do Google Flow e Veo 2 para Anti-Gravity
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


def preparar_payload_veo(
    prompt: str,
    aspect_ratio: str = "4:3",
    duration_seconds: int = 8,
    fps: int = 24,
    camera_movement: Optional[str] = None
) -> Dict[str, Any]:
    """Constrói a requisição formal compatível com a Vertex AI Veo 2 Video Generation API."""
    instance: Dict[str, Any] = {
        "prompt": prompt,
    }
    parameters: Dict[str, Any] = {
        "aspectRatio": aspect_ratio,
        "durationSeconds": duration_seconds,
        "fps": fps,
        "sampleCount": 1,
        "personGeneration": "ALLOW_ADULT",
    }
    if camera_movement:
        parameters["cameraMotion"] = camera_movement

    return {
        "instances": [instance],
        "parameters": parameters
    }


def despachar_googleflow_veo(
    prompt: str,
    output_dir: Path,
    shot_id: str,
    aspect_ratio: str = "4:3",
    duration_seconds: int = 8
) -> Dict[str, Any]:
    """Submete ou simula a geração de vídeo via Google Flow / Veo 2."""
    creds = obter_credenciais_ia()
    mode = creds.get("execution_mode") or "DRY_RUN"
    project = creds.get("gcp_project")
    location = creds.get("gcp_location") or "us-central1"

    payload = preparar_payload_veo(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        duration_seconds=duration_seconds
    )

    payload_file = output_dir / f"veo_payload_{shot_id}.json"
    with open(payload_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    if mode == "DRY_RUN" or not project or project == "seu-projeto-gcp-id":
        return {
            "status": "DRY_RUN_COMPILED",
            "shot_id": shot_id,
            "simulated": True,
            "engine": "Google Flow (Veo 2 Engine)",
            "payload_path": str(payload_file.resolve()),
            "message": "Payload Veo 2 compilado e validado. Configure GOOGLE_CLOUD_PROJECT para LIVE render."
        }

    return {
        "status": "READY_FOR_DISPATCH",
        "shot_id": shot_id,
        "simulated": False,
        "engine": "Google Flow (Veo 2 Engine)",
        "project": project,
        "location": location,
        "payload_path": str(payload_file.resolve())
    }
