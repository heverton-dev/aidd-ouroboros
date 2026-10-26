from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Garantir acesso a motores no path
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from motores.governanca.handoff_crypto import criar_envelope_handoff


def parse_args() -> tuple[Path, Path]:
    if len(sys.argv) >= 3 and not sys.argv[1].startswith("-"):
        return Path(sys.argv[1]), Path(sys.argv[2])
    
    parser = argparse.ArgumentParser(description="Nó 01: Geração de Roteiro e Storyboard")
    parser.add_argument("--input", "-i", type=str, default="context/input/pipeline_input.json")
    parser.add_argument("--output", "-o", type=str, default="context/handoffs/01_storyboard")
    args = parser.parse_args()
    return Path(args.input), Path(args.output)


def gerar_storyboard(config: Dict[str, Any]) -> Dict[str, Any]:
    topic = config.get("topic", "Narrativa Desconhecida")
    genre = config.get("genre", "sci-fi mystery")
    style = config.get("visual_style", "cinematic photorealistic 8k")
    aspect = config.get("aspect_ratio", "16:9")
    twist = config.get("ending_twist", "revelacao inesperada")
    duration = int(config.get("duration_seconds", 60))
    
    num_scenes = 30
    duration_per_scene = round(duration / num_scenes, 2)
    
    scenes: List[Dict[str, Any]] = []
    
    acts = [
        {"nome": "Ato 1: O Chamado e o Hook", "range": (1, 6), "tom": "tenso e misterioso"},
        {"nome": "Ato 2: A Investigacao do Sinal", "range": (7, 18), "tom": "crescente e obsessivo"},
        {"nome": "Ato 3: O Climax e Revelacao", "range": (19, 26), "tom": "frenetico e revelador"},
        {"nome": "Ato 4: O Twist e Conclusao", "range": (27, 30), "tom": "solene e impactante"},
    ]
    
    for i in range(1, num_scenes + 1):
        act_atual = next(a["nome"] for a in acts if a["range"][0] <= i <= a["range"][1])
        
        if i == 1:
            narration = f"No vasto silencio de Kepler, a frequencia nunca ouvida comeca a pulsar: {topic}."
            hook_strength = 1.0
        elif i == 30:
            narration = f"A transmissao final sela a verdade: {twist}."
            hook_strength = 0.95
        elif i == 15:
            narration = f"Decodificando as camadas quanticas, o padrao se revela artificial e aterrorizante."
            hook_strength = 0.8
        else:
            narration = f"Fase de decodificacao {i}: o espectro visual expande as coordenadas sob estetica {genre}."
            hook_strength = 0.5 + (i / 100.0)
            
        visual_prompt = (
            f"Scene {i:02d}: {act_atual}, {genre}, showing {topic}. "
            f"Visual details: {style}, shot angle dramatic, aspect ratio {aspect}, highly detailed."
        )
        
        scenes.append({
            "scene_id": i,
            "act": act_atual,
            "duration_seconds": duration_per_scene,
            "narration_text": narration,
            "visual_prompt": visual_prompt,
            "hook_strength": round(hook_strength, 2),
            "camera_directive": "slow push-in" if i % 2 == 1 else "pan right subtle"
        })
        
    return {
        "metadata": {
            "node_name": "node_01_story_script",
            "topic": topic,
            "genre": genre,
            "total_scenes": num_scenes,
            "total_duration_seconds": duration,
            "aspect_ratio": aspect,
            "ending_twist": twist
        },
        "characters": [
            {"id": "char_01", "name": "Dra. Elena Vance", "role": "Astrofisica Chefe", "traits": "olhar cansado, jaleco tecnologico azul escuro"},
            {"id": "char_02", "name": "Unidade AETHON", "role": "IA Receptora Central", "traits": "monolitica, nucleo de fusao reativo azulado"}
        ],
        "environments": [
            {"id": "env_01", "name": "Observatorio Atacama Deep-Space", "traits": "antenas parabolicas gigantes sob ceu estrelado"},
            {"id": "env_02", "name": "Sala de Processamento Quantico", "traits": "terminais holograficos translúcidos e servidores resfriados a nitrogenio"}
        ],
        "scenes": scenes
    }


def main() -> int:
    input_file, output_dir = parse_args()
    
    if not input_file.exists():
        sys.stderr.write(f"Erro: Arquivo de entrada nao encontrado: {input_file}\n")
        return 1
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(input_file, "r", encoding="utf-8") as f:
        input_data = json.load(f)
        
    storyboard = gerar_storyboard(input_data)
    
    storyboard_path = output_dir / "storyboard.json"
    with open(storyboard_path, "w", encoding="utf-8") as f:
        json.dump(storyboard, f, indent=2, ensure_ascii=False)
        
    payload_hash = hashlib.sha256(storyboard_path.read_bytes()).hexdigest()
    manifest = {
        "node": "node_01_story_script",
        "status": "COMPLETED",
        "output_files": [
            {"path": str(storyboard_path.relative_to(output_dir)), "sha256": payload_hash}
        ],
        "scene_count": len(storyboard["scenes"]),
        "total_duration": storyboard["metadata"]["total_duration_seconds"]
    }
    
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    criar_envelope_handoff(
        origem_skill="node_01_story_script",
        status_ou_artefatos="SUCCESS",
        artefatos_ou_metadados={
            "storyboard": str(storyboard_path),
            "manifest": str(manifest_path)
        },
        metadados=manifest,
        caminho_saida=output_dir / "HANDOFF.json"
    )
    print(f"[OK] Nó 01 concluido com sucesso. 30 cenas geradas em: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
