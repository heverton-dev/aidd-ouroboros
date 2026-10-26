#!/usr/bin/env python3
"""
Node 05: Multitrack Timeline Assembly & Delivery (Google Flow / ANTIGRAVITY)
Consolida multipistas de video gerado, narracao TTS, trilha sonora BGM,
sound effects (SFX) pontuais e gera legendas sincronizadas (.srt).
Emite o manifesto final do pipeline e exporta pipeline_output.json.
Zero Stubs, HMAC-SHA256, Pointer Architecture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from motores.governanca.handoff_crypto import create_handoff_envelope, verify_handoff_envelope


def format_srt_timestamp(seconds: float) -> str:
    """Converte segundos float para formato de legenda SRT (HH:MM:SS,mmm)."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milli = int(round((seconds - int(seconds)) * 1000))
    if milli >= 1000:
        milli = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{milli:03d}"


def load_input_data(input_path: Path) -> Dict[str, Any]:
    """Carrega dados brutos ou envelope HMAC de entrada resolvendo ponteiros canonicos."""
    if input_path.is_dir():
        for candidate in ["04_motion.json", "motion.json", "HANDOFF.json"]:
            cand_path = input_path / candidate
            if cand_path.exists():
                input_path = cand_path
                break

    with open(input_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    if "hmac_sha256" in payload and "payload" in payload:
        is_valid, msg = verify_handoff_envelope(payload)
        if not is_valid:
            print(f"[Node 05] AVISO: Falha na verificacao HMAC do handoff de entrada: {msg}")
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
        sibling = input_path.parent / "04_motion.json"
        if sibling.exists():
            with open(sibling, "r", encoding="utf-8") as sf:
                return json.load(sf)
        return inner

    if "envelope_hash" in payload and "data" in payload:
        is_valid, msg = verify_handoff_envelope(payload)
        if not is_valid:
            print(f"[Node 05] AVISO: Falha na verificacao HMAC do handoff de entrada: {msg}")
        return payload["data"]
    return payload


def retrieve_script_and_audio_context(pipeline_dir: Path) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Recupera dados dos nós 01 (roteiro) e 02 (áudio) a partir dos handoffs."""
    p = pipeline_dir.resolve()
    while p.name != "google-flow-story-video" and p != p.parent:
        p = p.parent
    if p.name == "google-flow-story-video":
        base_dir = p
    else:
        base_dir = REPO_ROOT / "aidd-pipelines" / "google-flow-story-video"

    dir_01 = base_dir / "context" / "handoffs" / "01_story_script"
    dir_02 = base_dir / "context" / "handoffs" / "02_tts_voiceover"

    script_data: Dict[str, Any] = {}
    audio_data: Dict[str, Any] = {}

    for cand_name in ["storyboard.json", "HANDOFF.json", "01_story_script.json"]:
        cand_path = dir_01 / cand_name
        if cand_path.exists():
            with open(cand_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if "hmac_sha256" in raw and "payload" in raw:
                    inner = raw["payload"]
                    if "artifacts_pointers" in inner and "principal" in inner["artifacts_pointers"]:
                        p_file = (dir_01 / inner["artifacts_pointers"]["principal"]["path"]).resolve()
                        if p_file.exists():
                            with open(p_file, "r", encoding="utf-8") as pf:
                                script_data = json.load(pf)
                                break
                    script_data = inner.get("data", inner)
                else:
                    script_data = raw.get("data", raw)
                if "scenes" in script_data:
                    break

    for cand_name in ["narration.json", "HANDOFF.json", "02_tts_voiceover.json"]:
        cand_path = dir_02 / cand_name
        if cand_path.exists():
            with open(cand_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if "hmac_sha256" in raw and "payload" in raw:
                    inner = raw["payload"]
                    if "artifacts_pointers" in inner and "principal" in inner["artifacts_pointers"]:
                        p_file = (dir_02 / inner["artifacts_pointers"]["principal"]["path"]).resolve()
                        if p_file.exists():
                            with open(p_file, "r", encoding="utf-8") as pf:
                                audio_data = json.load(pf)
                                break
                    audio_data = inner.get("data", inner)
                else:
                    audio_data = raw.get("data", raw)
                if "scenes" in audio_data:
                    break

    return script_data, audio_data


def assemble_timeline(motion_data: Dict[str, Any], pipeline_dir: Path) -> tuple[Dict[str, Any], str]:
    """
    Monta a linha do tempo sincronizada multipistas com vídeo, narração,
    trilha sonora orquestrada e sound effects procedurais.
    """
    script_data, audio_data = retrieve_script_and_audio_context(pipeline_dir)

    scenes_motion = motion_data.get("scenes", [])
    timeline_tracks: Dict[str, List[Dict[str, Any]]] = {
        "video_track": [],
        "voiceover_track": [],
        "sfx_track": [],
        "bgm_track": [],
    }

    current_time = 0.0
    srt_lines: List[str] = []
    srt_counter = 1

    script_scenes_map = {str(sc.get("scene_id")): sc for sc in script_data.get("scenes", [])}
    audio_scenes_map = {str(sc.get("scene_id")): sc for sc in audio_data.get("scenes", [])}

    for idx, motion_sc in enumerate(scenes_motion):
        scene_id = motion_sc.get("scene_id", f"scene_{idx + 1:03d}")
        duration = float(motion_sc.get("duration_seconds", 4.0))

        start_time = round(current_time, 2)
        end_time = round(current_time + duration, 2)

        video_clip = {
            "track_id": "V1",
            "scene_id": scene_id,
            "scene_index": idx + 1,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "camera_motion": motion_sc.get("camera_motion"),
            "lighting_dynamic": motion_sc.get("lighting_dynamic"),
            "transition": "crossfade" if idx > 0 else "fade_in_from_black",
            "transition_duration": 0.5 if idx > 0 else 0.8,
        }
        timeline_tracks["video_track"].append(video_clip)

        sc_key = str(scene_id)
        clean_num = "".join(filter(str.isdigit, sc_key))
        sc_text = ""
        if sc_key in script_scenes_map:
            sc_text = script_scenes_map[sc_key].get("narration_text", "")
        elif clean_num and clean_num in script_scenes_map:
            sc_text = script_scenes_map[clean_num].get("narration_text", "")
        elif sc_key in audio_scenes_map:
            sc_text = audio_scenes_map[sc_key].get("narration_text", "")
        elif clean_num and clean_num in audio_scenes_map:
            sc_text = audio_scenes_map[clean_num].get("narration_text", "")
        elif idx < len(script_data.get("scenes", [])):
            sc_text = script_data["scenes"][idx].get("narration_text", "")
        elif idx < len(audio_data.get("scenes", [])):
            sc_text = audio_data["scenes"][idx].get("narration_text", "")

        if not sc_text:
            sc_text = f"Cena {idx + 1}: Transmissao Kepler-22b"

        audio_clip = {
            "track_id": "A1_VOICE",
            "scene_id": scene_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "narration_text": sc_text,
            "volume_db": 0.0,
        }
        timeline_tracks["voiceover_track"].append(audio_clip)

        if sc_text:
            srt_start = format_srt_timestamp(start_time)
            srt_end = format_srt_timestamp(end_time)
            srt_lines.append(f"{srt_counter}\n{srt_start} --> {srt_end}\n{sc_text}\n")
            srt_counter += 1

        if idx in [0, 5, 14, 28, 29]:
            sfx_name = "sub_bass_drop" if idx == 0 else ("tachyon_burst" if idx == 14 else "cliffhanger_drone")
            timeline_tracks["sfx_track"].append(
                {
                    "track_id": "A2_SFX",
                    "scene_id": scene_id,
                    "sfx_name": sfx_name,
                    "start_time": start_time,
                    "duration": 2.5,
                    "volume_db": -6.0,
                }
            )

        current_time += duration

    total_duration = round(current_time, 2)

    timeline_tracks["bgm_track"].append(
        {
            "track_id": "A3_BGM",
            "track_name": "ouroboros_cybernetic_dark_ambient",
            "start_time": 0.0,
            "end_time": total_duration,
            "duration": total_duration,
            "ducking_against": "A1_VOICE",
            "ducking_volume_db": -18.0,
            "base_volume_db": -12.0,
        }
    )

    manifest = {
        "pipeline": "google-flow-story-video",
        "node": "node_05_timeline_assembly",
        "status": "COMPLETED",
        "total_duration_seconds": total_duration,
        "total_scenes": len(scenes_motion),
        "timeline_resolution": "1920x1080" if motion_data.get("aspect_ratio") == "16:9" else "1080x1920",
        "fps": 24,
        "tracks": timeline_tracks,
    }

    srt_content = "\n".join(srt_lines)
    return manifest, srt_content


def execute_node_05(input_path: Path, output_dir: Path) -> Path:
    """Execucao deterministica do no 05 com geracao de handoff HMAC e srt."""
    output_dir.mkdir(parents=True, exist_ok=True)
    p = output_dir.resolve()
    while p.name != "google-flow-story-video" and p != p.parent:
        p = p.parent
    if p.name == "google-flow-story-video":
        pipeline_dir = p
    else:
        pipeline_dir = REPO_ROOT / "aidd-pipelines" / "google-flow-story-video"
    motion_payload = load_input_data(input_path)

    timeline_result, srt_content = assemble_timeline(motion_payload, pipeline_dir)

    timeline_file = output_dir / "05_timeline.json"
    with open(timeline_file, "w", encoding="utf-8") as f:
        json.dump(timeline_result, f, indent=2, ensure_ascii=False)

    srt_file = output_dir / "timeline.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(srt_content)

    # Exportacao para Remotion (props prontas para Player / Bundler React)
    fps = timeline_result.get("fps", 24)
    res = timeline_result.get("timeline_resolution", "1080x1920").split("x")
    width = int(res[0])
    height = int(res[1])
    total_frames = int(timeline_result.get("total_duration_seconds", 60.0) * fps)

    remotion_scenes = []
    for sc in timeline_result.get("tracks", {}).get("video_track", []):
        d_sec = sc.get("duration", 2.0)
        remotion_scenes.append({
            "scene_id": sc.get("scene_id"),
            "order": sc.get("order"),
            "durationInFrames": int(d_sec * fps),
            "startFrame": int(sc.get("start_time", 0.0) * fps),
            "image": sc.get("source_image"),
            "narrationAudio": sc.get("audio_file"),
            "subtitle": sc.get("narration_text"),
            "cameraMotion": sc.get("camera_motion", {}),
            "aspectRatio": sc.get("aspect_ratio", "9:16"),
        })

    remotion_props = {
        "title": "Google Flow Story Film",
        "fps": fps,
        "width": width,
        "height": height,
        "durationInFrames": total_frames,
        "scenes": remotion_scenes,
        "audioTracks": {
            "voiceoverVolume": 1.0,
            "backgroundMusicVolume": 0.15,
            "duckingEnabled": True
        }
    }

    remotion_file = output_dir / "remotion_props.json"
    with open(remotion_file, "w", encoding="utf-8") as f:
        json.dump(remotion_props, f, indent=2, ensure_ascii=False)

    # Concat Demuxer do FFmpeg integrando os frames reais de cena do No 03 e audio do No 02
    images_dir = pipeline_dir / "context" / "handoffs" / "03_visual_assets" / "images"
    audio_file = pipeline_dir / "context" / "handoffs" / "02_tts_voiceover" / "audio.wav"
    concat_file = output_dir / "input_images.txt"
    output_mp4 = output_dir / "output_story.mp4"

    # Fallback defensivo para audio.wav se nao gerado anteriormente
    if not audio_file.exists():
        tts_dir = pipeline_dir / "context" / "handoffs" / "02_tts_voiceover"
        audio_sub = tts_dir / "audio"
        search_dirs = [audio_sub, tts_dir]
        mp3_files: List[Path] = []
        for sdir in search_dirs:
            if sdir.exists():
                found = sorted(list(sdir.glob("scene_*.mp3")))
                if found:
                    mp3_files = found
                    break
        if mp3_files:
            audio_concat_txt = tts_dir / "audio_concat.txt"
            with open(audio_concat_txt, "w", encoding="utf-8") as acf:
                for af in mp3_files:
                    acf.write(f"file '{af.resolve().as_posix()}'\n")
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(audio_concat_txt), "-c:a", "pcm_s16le", str(audio_file)],
                    cwd=str(tts_dir),
                    capture_output=True,
                    text=True,
                    check=True
                )
                print(f"[Node 05] Fallback: audio.wav gerado a partir de {len(mp3_files)} faixas MP3.")
            except Exception as concat_err:
                print(f"[Node 05] Erro ao consolidar audio.wav: {concat_err}")

    video_scenes = timeline_result.get("tracks", {}).get("video_track", [])
    concat_lines = []
    for sc in video_scenes:
        idx = sc.get("scene_index", 1)
        dur = sc.get("duration", 4.0)
        img_name = f"scene_{idx:02d}_frame.png"
        img_path = images_dir / img_name
        if not img_path.exists():
            img_path = images_dir / f"scene_{idx:03d}_frame.png"
        concat_lines.append(f"file '{img_path.resolve().as_posix()}'")
        concat_lines.append(f"duration {dur}")

    if video_scenes:
        last_idx = video_scenes[-1].get("scene_index", len(video_scenes))
        last_img = images_dir / f"scene_{last_idx:02d}_frame.png"
        if not last_img.exists():
            last_img = images_dir / f"scene_{last_idx:03d}_frame.png"
        concat_lines.append(f"file '{last_img.resolve().as_posix()}'")

    with open(concat_file, "w", encoding="utf-8") as f:
        f.write("\n".join(concat_lines) + "\n")

    # Script deterministico FFmpeg para renderizacao direta headless
    ffmpeg_bat_file = output_dir / "render_ffmpeg.bat"
    ffmpeg_ps1_file = output_dir / "render_ffmpeg.ps1"
    
    bat_content = f"""@echo off
REM Renderizador Headless Deterministico FFmpeg - Ouroboros Pipeline
echo [Ouroboros] Iniciando montagem headless com FFmpeg...
REM Utiliza concat demuxer com os frames de cena e audio sincronizado
ffmpeg -y -f concat -safe 0 -i input_images.txt -i "{audio_file.resolve().as_posix()}" -vf "subtitles=timeline.srt:force_style='FontSize=20,PrimaryColour=&HFFFFFF,BackColour=&H80000000,BorderStyle=4'" -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest output_story.mp4
echo [Ouroboros] Render concluido: output_story.mp4
"""
    with open(ffmpeg_bat_file, "w", encoding="utf-8") as f:
        f.write(bat_content)

    ps1_content = f"""# Renderizador Headless Deterministico FFmpeg - Ouroboros Pipeline
Write-Host "[Ouroboros] Iniciando montagem headless com FFmpeg..." -ForegroundColor Cyan
ffmpeg -y -f concat -safe 0 -i input_images.txt -i "{audio_file.resolve().as_posix()}" -vf "subtitles=timeline.srt:force_style='FontSize=20,PrimaryColour=&HFFFFFF,BackColour=&H80000000,BorderStyle=4'" -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest output_story.mp4
Write-Host "[Ouroboros] Render concluido: output_story.mp4" -ForegroundColor Green
"""
    with open(ffmpeg_ps1_file, "w", encoding="utf-8") as f:
        f.write(ps1_content)

    # Execucao nativa direta do FFmpeg se disponivel no ambiente
    try:
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", "input_images.txt",
            "-i", str(audio_file.resolve()),
            "-vf", "subtitles=timeline.srt:force_style='FontSize=20,PrimaryColour=&HFFFFFF,BackColour=&H80000000,BorderStyle=4'",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "output_story.mp4"
        ]
        res = subprocess.run(cmd, cwd=str(output_dir), capture_output=True, text=True, check=True)
        print("[Node 05] Render FFmpeg com legendas concluido: output_story.mp4")
    except Exception as exc:
        print(f"[Node 05] Aviso no render com legendas ({exc}). Tentando fallback FFmpeg direto...")
        try:
            cmd_fallback = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", "input_images.txt",
                "-i", str(audio_file.resolve()),
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                "output_story.mp4"
            ]
            res_fb = subprocess.run(cmd_fallback, cwd=str(output_dir), capture_output=True, text=True, check=True)
            print("[Node 05] Render FFmpeg fallback concluido com sucesso: output_story.mp4")
        except Exception as fb_exc:
            print(f"[Node 05] Erro critico no render fallback do FFmpeg: {fb_exc}")

    final_output_file = pipeline_dir / "context" / "output" / "pipeline_output.json"
    final_output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(final_output_file, "w", encoding="utf-8") as f:
        json.dump(timeline_result, f, indent=2, ensure_ascii=False)

    final_mp4_export = pipeline_dir / "context" / "output" / "output_story.mp4"
    if output_mp4.exists():
        try:
            shutil.copy2(output_mp4, final_mp4_export)
        except Exception as cperr:
            print(f"[Node 05] Erro ao copiar output_story.mp4 para context/output: {cperr}")

    artifacts_to_seal = [
        str(timeline_file),
        str(srt_file),
        str(remotion_file),
        str(concat_file),
        str(ffmpeg_bat_file),
        str(ffmpeg_ps1_file),
        str(final_output_file),
    ]
    if output_mp4.exists():
        artifacts_to_seal.append(str(output_mp4))
    if final_mp4_export.exists():
        artifacts_to_seal.append(str(final_mp4_export))

    handoff_envelope = create_handoff_envelope(
        source_skill="aidd-pipelines/google-flow-story-video/node_05_timeline_assembly",
        target_skill="aidd-pipelines/google-flow-story-video/final_delivery",
        payload_data=timeline_result,
        local_artifacts=artifacts_to_seal,
        metadata={"step": 5, "total_steps": 5, "type": "timeline_assembly_completed"},
    )

    handoff_file = output_dir / "HANDOFF.json"
    with open(handoff_file, "w", encoding="utf-8") as f:
        json.dump(handoff_envelope, f, indent=2, ensure_ascii=False)

    print(f"[Node 05] Montagem da timeline concluida. Duracao total: {timeline_result['total_duration_seconds']}s.")
    print(f"[Node 05] Legendas SRT e pipeline_output.json consolidados com sucesso.")
    return handoff_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Node 05: Multitrack Timeline Assembly")
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
            / "04_motion_synthesis"
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
                / "04_motion_synthesis"
                / "04_motion.json"
            )

    if not output_dir:
        output_dir = str(
            REPO_ROOT
            / "aidd-pipelines"
            / "google-flow-story-video"
            / "context"
            / "handoffs"
            / "05_timeline_assembly"
        )

    execute_node_05(Path(input_file), Path(output_dir))


if __name__ == "__main__":
    main()
