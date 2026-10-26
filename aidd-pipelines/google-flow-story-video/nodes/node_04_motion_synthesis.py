#!/usr/bin/env python3
"""
Node 04: Motion Synthesis & Camera Prompting (Google Flow / ANTIGRAVITY)
Define trajetorias cineticas de camera, dinamica de iluminacao volumetrica
e sintetiza prompts de video para motores neurais (Kling / Luma / Haiper).
Zero Stubs, HMAC-SHA256, Pointer Architecture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from motores.governanca.handoff_crypto import create_handoff_envelope, verify_handoff_envelope

CAMERA_MOTIONS: List[str] = [
    "Slow smooth cinematic push-in forward (dolly in), focal length 35mm",
    "Subtle cinematic orbit arc pan left-to-right, maintaining subject center",
    "Steady tracking shot gliding backwards (dolly out), revealing environment",
    "Low angle upward tilt with volumetric atmospheric haze, anamorphic flare",
    "Handheld slight organic drift, tense close-up focus with rack focus shift",
    "Dynamic crane descent settling into medium profile angle",
]

LIGHTING_DYNAMICS: List[str] = [
    "Volumetric cold blue rim light counterbalanced by warm amber key light",
    "Flickering holographic neon luminescence casting sharp specular highlights",
    "High-contrast chiaroscuro shadows with dynamic tachyon particle diffusion",
    "Deep ambient shadows pierced by intense directional ultraviolet beams",
    "Subtle cinematic dusk grading with golden hour god-rays piercing dust motes",
]


def load_input_data(input_path: Path) -> Dict[str, Any]:
    """Carrega dados brutos ou envelope HMAC de entrada resolvendo ponteiros canonicos."""
    if input_path.is_dir():
        for candidate in ["visual_assets.json", "03_visual_assets.json", "HANDOFF.json"]:
            cand_path = input_path / candidate
            if cand_path.exists():
                input_path = cand_path
                break

    with open(input_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if "hmac_sha256" in payload and "payload" in payload:
        is_valid, msg = verify_handoff_envelope(payload)
        if not is_valid:
            print(f"[Node 04] AVISO: Falha na verificacao HMAC do handoff de entrada: {msg}")
        inner = payload["payload"]
        if "artifacts_pointers" in inner and "principal" in inner["artifacts_pointers"]:
            p_path = Path(inner["artifacts_pointers"]["principal"]["path"])
            if not p_path.is_absolute():
                p_path = (input_path.parent / p_path).resolve()
            if p_path.exists():
                with open(p_path, "r", encoding="utf-8") as pf:
                    return json.load(pf)
        if "data" in inner and isinstance(inner["data"], dict) and "scenes" in inner["data"]:
            return inner["data"]
        # Se for o próprio envelope sem scenes, tentar carregar o arquivo irmao visual_assets.json
        sibling = input_path.parent / "visual_assets.json"
        if sibling.exists():
            with open(sibling, "r", encoding="utf-8") as sf:
                return json.load(sf)
        return inner

    if "envelope_hash" in payload and "data" in payload:
        is_valid, msg = verify_handoff_envelope(payload)
        if not is_valid:
            print(f"[Node 04] AVISO: Falha na verificacao HMAC do handoff de entrada: {msg}")
        return payload["data"]

    return payload


def generate_motion_synthesis(visual_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sintetiza especificacoes de movimento cinetico, camera e iluminacao
    para cada cena gerada no no 03.
    """
    scenes = visual_data.get("scenes", [])
    motion_scenes: List[Dict[str, Any]] = []

    for idx, sc in enumerate(scenes):
        scene_id = sc.get("scene_id", f"scene_{idx + 1:03d}")
        duration = float(sc.get("target_duration_seconds", 4.0))
        camera_profile = CAMERA_MOTIONS[idx % len(CAMERA_MOTIONS)]
        lighting_profile = LIGHTING_DYNAMICS[idx % len(LIGHTING_DYNAMICS)]

        seed_base = int(sc.get("seed", 42000))
        speed_factor = 1.0 if duration >= 3.5 else 1.25

        motion_prompt = (
            f"{sc.get('image_prompt', '')}. Camera dynamic: {camera_profile}. "
            f"Atmosphere & Lighting: {lighting_profile}. Motion intensity: smooth 24fps filmic realism."
        )

        motion_entry = {
            "scene_id": scene_id,
            "scene_index": idx + 1,
            "duration_seconds": duration,
            "seed": seed_base,
            "camera_motion": camera_profile,
            "lighting_dynamic": lighting_profile,
            "speed_multiplier": speed_factor,
            "optical_flow_tracking": True,
            "depth_map_guidance": "MiDaS_v3_hybrid",
            "video_generation_prompt": motion_prompt,
            "engine_target": "kling-v1.6-pro",
            "fps": 24,
            "motion_bucket_id": 127 + (idx % 20),
        }
        motion_scenes.append(motion_entry)

    manifest = {
        "pipeline": "google-flow-story-video",
        "node": "node_04_motion_synthesis",
        "status": "COMPLETED",
        "total_motion_scenes": len(motion_scenes),
        "visual_style": visual_data.get("visual_style", "Cinematic Cyberpunk"),
        "aspect_ratio": visual_data.get("aspect_ratio", "16:9"),
        "scenes": motion_scenes,
    }
    return manifest


def execute_node_04(input_path: Path, output_dir: Path) -> Path:
    """Execucao deterministica do no 04 com geracao de handoff HMAC."""
    output_dir.mkdir(parents=True, exist_ok=True)
    visual_payload = load_input_data(input_path)

    motion_result = generate_motion_synthesis(visual_payload)

    motion_file = output_dir / "04_motion.json"
    with open(motion_file, "w", encoding="utf-8") as f:
        json.dump(motion_result, f, indent=2, ensure_ascii=False)

    handoff_envelope = create_handoff_envelope(
        source_skill="aidd-pipelines/google-flow-story-video/node_04_motion_synthesis",
        target_skill="aidd-pipelines/google-flow-story-video/node_05_timeline_assembly",
        payload_data=motion_result,
        local_artifacts=[str(motion_file)],
        metadata={"step": 4, "total_steps": 5, "type": "motion_synthesis"},
    )

    handoff_file = output_dir / "HANDOFF.json"
    with open(handoff_file, "w", encoding="utf-8") as f:
        json.dump(handoff_envelope, f, indent=2, ensure_ascii=False)

    print(f"[Node 04] Sintese de movimento cinemático concluida: {len(motion_result['scenes'])} cenas.")
    print(f"[Node 04] Saidas salvas em: {output_dir}")
    return handoff_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Node 04: Motion Synthesis & Camera Trajectories")
    parser.add_argument("pos_input", nargs="?", default=None, help="Caminho do arquivo de entrada posicional")
    parser.add_argument("pos_output", nargs="?", default=None, help="Diretorio de saida posicional")
    parser.add_argument("--input", "-i", dest="flag_input", default=None, help="Caminho do arquivo de entrada")
    parser.add_argument("--output", "-o", dest="flag_output", default=None, help="Diretorio de saida")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_file = args.flag_input or args.pos_input
    output_dir = args.flag_output or args.pos_output

    if not input_file:
        default_in = (
            REPO_ROOT
            / "aidd-pipelines"
            / "google-flow-story-video"
            / "context"
            / "handoffs"
            / "03_visual_assets"
            / "HANDOFF.json"
        )
        if default_in.exists():
            input_file = str(default_in)
        else:
            input_file = str(
                REPO_ROOT
                / "aidd-pipelines"
                / "google-flow-story-video"
                / "context"
                / "handoffs"
                / "03_visual_assets"
                / "03_visual_assets.json"
            )

    if not output_dir:
        output_dir = str(
            REPO_ROOT
            / "aidd-pipelines"
            / "google-flow-story-video"
            / "context"
            / "handoffs"
            / "04_motion_synthesis"
        )

    execute_node_04(Path(input_file), Path(output_dir))


if __name__ == "__main__":
    main()
