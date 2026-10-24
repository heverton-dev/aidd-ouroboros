#!/usr/bin/env python3
"""
scripts/hybrid_stitch.py
Pipeline híbrido de composição e stitching que une capturas do Playwright
com animações conceituais do Remotion via FFmpeg (TK-04).
"""

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional


def detect_scene_engine(scene: Dict[str, Any]) -> str:
    """Identifica se uma cena do spec.json deve ser renderizada pelo Remotion ou Playwright."""
    engine = scene.get("engine", "").lower()
    layout = scene.get("layout", "").lower()

    if engine == "remotion" or layout in ("animacao_conceitual", "remotion", "diagram"):
        return "remotion"
    return "playwright"


def build_remotion_render_command(
    entry_point: Path,
    composition_id: str,
    out_file: Path,
    fps: int = 60,
    props_file: Optional[Path] = None,
) -> List[str]:
    """Constrói o comando CLI determinístico para renderizar uma composição Remotion."""
    cmd = [
        "npx",
        "remotion",
        "render",
        str(entry_point).replace("\\", "/"),
        composition_id,
        str(out_file).replace("\\", "/"),
        "--fps",
        str(fps),
    ]
    if props_file and props_file.exists():
        cmd.extend(["--props", str(props_file).replace("\\", "/")])
    return cmd


def generate_ffmpeg_concat_file(video_paths: List[Path], out_file: Path) -> Path:
    """Gera o arquivo de texto no formato exigido pelo demuxer concat do FFmpeg."""
    out_file = Path(out_file)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for vp in video_paths:
        vp_path = Path(vp)
        # Usa o nome do arquivo se estiverem no mesmo diretório, ou path absoluto escapado
        if vp_path.parent == out_file.parent:
            filename = vp_path.name
        else:
            filename = str(vp_path.resolve()).replace("\\", "/")
        lines.append(f"file '{filename}'")

    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_file


def run_ffmpeg_concat(concat_file: Path, output_video: Path) -> bool:
    """Executa a concatenação FFmpeg sem reencode quando possível."""
    output_video.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(output_video),
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback com re-encode se os codecs variarem entre Playwright e Remotion
        fallback_cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(output_video),
        ]
        res = subprocess.run(fallback_cmd, capture_output=True, text=True)
        return res.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline híbrido de montagem Playwright + Remotion via FFmpeg."
    )
    parser.add_argument(
        "--spec",
        "-s",
        required=True,
        type=Path,
        help="Caminho do spec.json ou storyboard.json.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("out/final_tutorial.mp4"),
        help="Caminho do arquivo final concatenado.",
    )

    args = parser.parse_args()

    if not args.spec.exists():
        print(f"[ERRO] Spec não encontrado: {args.spec}", file=sys.stderr)
        sys.exit(1)

    with open(args.spec, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenes = data.get("scenes", [])
    print(f"[*] Analisando {len(scenes)} cenas no spec...")

    for sc in scenes:
        engine = detect_scene_engine(sc)
        print(f"  - Cena [{sc.get('id', 'sem-id')}]: Motor = {engine}")


if __name__ == "__main__":
    main()
