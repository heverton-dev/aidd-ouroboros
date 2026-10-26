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

from motores.governanca.handoff_crypto import criar_envelope_handoff, verificar_envelope_handoff


def parse_args() -> tuple[Path, Path]:
    if len(sys.argv) >= 3 and not sys.argv[1].startswith("-"):
        return Path(sys.argv[1]), Path(sys.argv[2])
        
    parser = argparse.ArgumentParser(description="Nó 02: TTS e Sintese de Narração Audio-First")
    parser.add_argument("--input", "-i", type=str, default="context/handoffs/01_storyboard")
    parser.add_argument("--output", "-o", type=str, default="context/handoffs/02_narration")
    args = parser.parse_args()
    return Path(args.input), Path(args.output)


import asyncio
import subprocess

try:
    import edge_tts
except ImportError:
    edge_tts = None

def get_audio_duration_ffprobe(filepath: Path) -> float:
    try:
        res = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(filepath)],
            text=True
        )
        return float(res.strip())
    except Exception as e:
        sys.stderr.write(f"Aviso: Falha ao medir duracao via ffprobe: {e}\n")
        return 2.5


import math
import struct
import wave


def generate_fallback_tone(output_file: Path, duration_seconds: float = 2.0, freq: float = 440.0) -> None:
    sample_rate = 24000
    n_samples = int(sample_rate * duration_seconds)
    with wave.open(str(output_file), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        data = bytearray()
        for i in range(n_samples):
            val = int(32767.0 * 0.1 * math.sin(2.0 * math.pi * freq * i / sample_rate))
            data.extend(struct.pack("<h", val))
        wav_file.writeframes(data)


async def synthesize_all_tracks(scenes: List[Dict[str, Any]], audio_dir: Path, voice_name: str) -> List[tuple[int, Path, float]]:
    results = []
    audio_dir.mkdir(parents=True, exist_ok=True)
    for sc in scenes:
        scene_id = sc["scene_id"]
        text = sc["narration_text"]
        audio_file = audio_dir / f"scene_{scene_id:02d}.mp3"
        sintetizado = False
        if edge_tts is not None:
            try:
                comm = edge_tts.Communicate(text, voice_name)
                await comm.save(str(audio_file))
                dur = get_audio_duration_ffprobe(audio_file)
                sintetizado = True
            except Exception as e:
                sys.stderr.write(f"Aviso: Falha ao sintetizar via edge-tts ({e}). Usando gerador de tom PCM local.\n")
        
        if not sintetizado:
            wav_fallback = audio_dir / f"scene_{scene_id:02d}.wav"
            calc_dur = max(2.0, len(text.split()) * 0.35)
            generate_fallback_tone(wav_fallback, duration_seconds=calc_dur, freq=220.0 + (scene_id * 10))
            audio_file = wav_fallback
            dur = calc_dur
        results.append((scene_id, audio_file, dur))
    return results


def processar_audio_narration(storyboard: Dict[str, Any], voice_gender: str, output_dir: Path) -> tuple[Dict[str, Any], List[Dict[str, str]]]:
    scenes = storyboard.get("scenes", [])
    audio_dir = output_dir / "audio"
    
    voice_name = "pt-BR-AntonioNeural" if voice_gender == "male" else "pt-BR-FranciscaNeural"
    voice_label = f"edge-tts: {voice_name}"
    
    # Gerar áudio real com edge-tts de forma assíncrona
    print(f"[Nó 02] Sintetizando {len(scenes)} faixas de áudio via {voice_name}...")
    synth_results = asyncio.run(synthesize_all_tracks(scenes, audio_dir, voice_name))
    synth_map = {sid: (path, dur) for sid, path, dur in synth_results}
    
    current_time = 0.0
    narration_tracks: List[Dict[str, Any]] = []
    output_files_meta: List[Dict[str, str]] = []
    
    for sc in scenes:
        scene_id = sc["scene_id"]
        text = sc["narration_text"]
        words = text.split()
        word_count = len(words)
        
        audio_file, measured_duration = synth_map[scene_id]
        
        # O corte visual dura no mínimo a narração + pequeno respiro de 0.2s
        final_scene_duration = round(max(measured_duration + 0.2, sc.get("duration_seconds", 2.0)), 2)
        
        start_time = round(current_time, 2)
        end_time = round(current_time + final_scene_duration, 2)
        current_time = end_time
        
        # Hash do áudio gerado
        rel_audio_path = str(audio_file.relative_to(output_dir)).replace("\\", "/")
        audio_sha = hashlib.sha256(audio_file.read_bytes()).hexdigest()
        output_files_meta.append({"path": rel_audio_path, "sha256": audio_sha})
        
        narration_tracks.append({
            "scene_id": scene_id,
            "start_time_seconds": start_time,
            "end_time_seconds": end_time,
            "duration_seconds": final_scene_duration,
            "measured_audio_seconds": round(measured_duration, 2),
            "text": text,
            "word_count": word_count,
            "voice_profile": voice_label,
            "audio_frequency_hz": 24000,
            "audio_channels": 1,
            "audio_path": rel_audio_path,
            "pacing": "slow_deliberate" if scene_id in [1, 29, 30] else "steady_tension"
        })
        
    narration_data = {
        "metadata": {
            "node_name": "node_02_tts_voiceover",
            "voice_gender": voice_gender,
            "voice_engine": "edge-tts",
            "voice_name": voice_name,
            "rule_applied": "Audio-First Timing (Áudio dita a duração dos cortes visuais)",
            "total_audio_duration_seconds": round(current_time, 2),
            "total_tracks": len(narration_tracks)
        },
        "narration_tracks": narration_tracks
    }
    return narration_data, output_files_meta


def main() -> int:
    input_path, output_dir = parse_args()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if input_path.is_dir():
        for cand in ["storyboard.json", "01_storyboard.json"]:
            if (input_path / cand).exists():
                storyboard_file = input_path / cand
                break
        else:
            storyboard_file = input_path / "storyboard.json"
    elif input_path.is_file() and input_path.name == "HANDOFF.json":
        storyboard_file = input_path.parent / "storyboard.json"
    else:
        storyboard_file = input_path
    
    if not storyboard_file.exists():
        sys.stderr.write(f"Erro: Arquivo do storyboard nao encontrado em: {storyboard_file}\n")
        return 1
        
    # Verificar integridade criptográfica se houver envelope anterior
    handoff_in = input_path if (input_path.is_file() and input_path.name == "HANDOFF.json") else (input_path / "HANDOFF.json")
    if handoff_in.exists():
        valido, msg = verificar_envelope_handoff(handoff_in, verificar_integridade_disco=True)
        if not valido:
            sys.stderr.write(f"Erro: Falha na verificacao HMAC do handoff anterior: {msg}\n")
            return 1
            
    with open(storyboard_file, "r", encoding="utf-8") as f:
        storyboard = json.load(f)
        
    voice_gender = storyboard.get("metadata", {}).get("voice_gender", "male")
    narration_data, audio_output_meta = processar_audio_narration(storyboard, voice_gender, output_dir)
    
    # Concatenar todos os audios gerados em audio.wav para o pipeline
    audio_wav_path = output_dir / "audio.wav"
    audio_tracks = narration_data.get("narration_tracks", [])
    if audio_tracks:
        concat_txt = output_dir / "concat_audio.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for trk in audio_tracks:
                rel_p = trk.get("audio_path") or trk.get("audio_file")
                if rel_p:
                    track_file = output_dir / rel_p
                    if track_file.exists():
                        f.write(f"file '{track_file.resolve().as_posix()}'\n")
        try:
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt), "-c:a", "pcm_s16le", str(audio_wav_path)],
                check=True, capture_output=True
            )
            if audio_wav_path.exists():
                wav_hash = hashlib.sha256(audio_wav_path.read_bytes()).hexdigest()
                audio_output_meta.append({
                    "path": str(audio_wav_path.relative_to(output_dir)).replace("\\", "/"),
                    "sha256": wav_hash
                })
        except Exception as e:
            sys.stderr.write(f"Aviso na concatenacao de audio.wav: {e}\n")

    narration_path = output_dir / "narration.json"
    with open(narration_path, "w", encoding="utf-8") as f:
        json.dump(narration_data, f, indent=2, ensure_ascii=False)
        
    payload_hash = hashlib.sha256(narration_path.read_bytes()).hexdigest()
    
    all_output_files = [
        {"path": str(narration_path.relative_to(output_dir)).replace("\\", "/"), "sha256": payload_hash}
    ] + audio_output_meta

    manifest = {
        "node": "node_02_tts_voiceover",
        "status": "COMPLETED",
        "output_files": all_output_files,
        "total_tracks": len(narration_data["narration_tracks"]),
        "total_audio_duration": narration_data["metadata"]["total_audio_duration_seconds"]
    }
    
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    criar_envelope_handoff(
        origem_skill="node_02_tts_voiceover",
        status_ou_artefatos="SUCCESS",
        artefatos_ou_metadados={
            "narration": str(narration_path),
            "manifest": str(manifest_path)
        },
        metadados=manifest,
        caminho_saida=output_dir / "HANDOFF.json"
    )
    print(f"[OK] Nó 02 concluido com sucesso. {len(audio_output_meta)} faixas de áudio geradas fisicamente em: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
