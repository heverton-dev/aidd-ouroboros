#!/usr/bin/env python3
"""
scripts/whisper_to_remotion.py
Conversor determinístico de transcrição TSV do faster-whisper para keyframes de Remotion.
Parte do pipeline de tutoriais animados no método Viktor Kav (TK-03).
"""

import argparse
import csv
import json
from pathlib import Path
import sys
from typing import Any, Dict, List


def parse_timestamp_to_seconds(raw_val: str, units: str = "ms") -> float:
    """Converte string de timestamp (ms ou s) em float de segundos."""
    val = float(raw_val.strip())
    u = units.strip().lower()
    if u == "ms":
        return val / 1000.0
    elif u == "s":
        return val
    elif u == "auto":
        if val > 1000.0:
            return val / 1000.0
        return val
    else:
        raise ValueError(f"Unidade inválida: {units}. Escolha entre 'ms', 's' ou 'auto'.")


def convert_whisper_tsv_to_remotion_props(
    tsv_path: Path, fps: int = 60, units: str = "ms"
) -> Dict[str, Any]:
    """Lê TSV do Whisper e gera objeto de propriedades para a timeline do Remotion."""
    tsv_path = Path(tsv_path)
    if not tsv_path.exists():
        raise FileNotFoundError(f"Arquivo de transcrição não encontrado: {tsv_path}")

    events: List[Dict[str, Any]] = []
    max_frame = 0

    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)

        start_col = 0
        end_col = 1
        text_col = 2
        line_num = 1 if header else 0

        if header:
            for idx, col in enumerate(header):
                col_lower = col.strip().lower()
                if col_lower == "start":
                    start_col = idx
                elif col_lower == "end":
                    end_col = idx
                elif col_lower == "text":
                    text_col = idx

        for row_idx, row in enumerate(reader):
            line_num += 1
            if not row or len(row) <= max(start_col, end_col):
                continue

            try:
                start_sec = parse_timestamp_to_seconds(row[start_col], units=units)
                end_sec = parse_timestamp_to_seconds(row[end_col], units=units)
            except (ValueError, TypeError):
                continue

            if end_sec < start_sec:
                raise ValueError(f"Linha {line_num}: end ({end_sec}) < start ({start_sec})")

            text = row[text_col].strip() if len(row) > text_col else ""
            start_frame = int(round(start_sec * fps))
            end_frame = int(round(end_sec * fps))
            duration = max(1, end_frame - start_frame)

            if end_frame > max_frame:
                max_frame = end_frame

            events.append(
                {
                    "id": f"ev-{row_idx:03d}",
                    "text": text,
                    "startSeconds": round(start_sec, 3),
                    "endSeconds": round(end_sec, 3),
                    "startFrame": start_frame,
                    "endFrame": end_frame,
                    "durationInFrames": duration,
                }
            )

    return {
        "fps": fps,
        "totalDurationInFrames": max_frame,
        "events": events,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Converte transcrição TSV do Whisper para composition_props.json do Remotion."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        type=Path,
        help="Caminho do arquivo TSV gerado pelo whisper.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("composition_props.json"),
        help="Caminho do arquivo JSON de saída para o Remotion.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=60,
        help="Framerate do vídeo alvo (padrão: 60).",
    )
    parser.add_argument(
        "--units",
        choices=["ms", "s", "auto"],
        default="ms",
        help="Unidade dos timestamps no TSV (ms, s, auto). Padrão: ms.",
    )

    args = parser.parse_args()

    try:
        props = convert_whisper_tsv_to_remotion_props(
            args.input, fps=args.fps, units=args.units
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(props, f, indent=2, ensure_ascii=False)
        print(f"[OK] Gerado {args.output} com {len(props['events'])} eventos ({props['totalDurationInFrames']} frames @ {args.fps}fps)")
    except Exception as e:
        print(f"[ERRO] Falha na conversão: {e}", file=sys.stderr)
        sys.exit(1)
        sys.exit(1)


if __name__ == "__main__":
    main()
