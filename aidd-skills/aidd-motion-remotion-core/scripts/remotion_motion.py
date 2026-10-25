#!/usr/bin/env python3
"""
remotion_motion.py — Renderizador real e determinístico de motion graphics via Remotion.
Padrão: AIDD Universal Handoff + Zero Stubs + Validação ffprobe.
"""
import argparse
import hashlib
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aidd-motion-remotion-core")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REMOTION_ENGINE_DIR = PROJECT_ROOT / "motores" / "remotion"

# Importa governança de handoff
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from motores.governanca.handoff_crypto import abrir_handoff, selar_handoff


def get_remotion_runner() -> list[str]:
    """Retorna o executável disponível para disparar comandos Remotion."""
    if shutil.which("bun"):
        return ["bun", "run", "remotion"]
    if shutil.which("npx"):
        return ["npx", "remotion"]
    raise RuntimeError("Nenhum gerenciador de runtime (bun ou npx) encontrado no PATH.")


def check_doctor() -> bool:
    """Verifica a presença de binários, engines e dependências obrigatórias."""
    logger.info("=== [AIDD-REMOTION-MOTION] Diagnóstico de Ambiente (Doctor) ===")
    ok = True

    # 1. Checa ffprobe
    ffprobe_bin = shutil.which("ffprobe")
    if ffprobe_bin:
        logger.info("[+] ffprobe detectado: %s", ffprobe_bin)
    else:
        logger.error("[-] ffprobe NÃO encontrado no PATH.")
        ok = False

    # 2. Checa bun ou npx
    runner_ok = False
    for runner in ("bun", "npx"):
        found = shutil.which(runner)
        if found:
            logger.info("[+] Runtime CLI detectado: %s (%s)", runner, found)
            runner_ok = True
            break
    if not runner_ok:
        logger.error("[-] Nem 'bun' nem 'npx' foram encontrados no PATH.")
        ok = False

    # 3. Checa motores/remotion e node_modules
    if not REMOTION_ENGINE_DIR.exists():
        logger.error("[-] Diretório do motor Remotion não existe: %s", REMOTION_ENGINE_DIR)
        ok = False
    else:
        node_modules = REMOTION_ENGINE_DIR / "node_modules"
        if node_modules.exists() and any(node_modules.iterdir()):
            logger.info("[+] node_modules presente em: %s", node_modules)
        else:
            logger.error("[-] node_modules ausente ou vazio em: %s", REMOTION_ENGINE_DIR)
            ok = False

    if ok:
        logger.info("[OK] Ambiente validado com sucesso!")
    else:
        logger.error("[FALHA] Pré-requisitos não atendidos.")
    return ok


def validate_video_with_ffprobe(video_path: Path) -> dict:
    """Inspeciona o vídeo com ffprobe e assegura codec h264 e duração positiva."""
    if not video_path.exists():
        raise FileNotFoundError(f"Vídeo para inspeção não encontrado: {video_path}")

    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=codec_name",
        "-show_entries", "format=duration",
        "-of", "json",
        str(video_path.resolve())
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe falhou ao inspecionar {video_path}: {result.stderr.strip()}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"ffprobe retornou saída JSON inválida: {result.stdout}") from exc

    streams = data.get("streams", [])
    if not streams:
        raise ValueError(f"ffprobe não encontrou stream de vídeo em {video_path}")

    codec = streams[0].get("codec_name", "").lower()
    if codec not in ("h264", "avc1"):
        raise ValueError(f"Codec esperado h264/avc1, obtido: {codec}")

    format_info = data.get("format", {})
    try:
        duration_s = float(format_info.get("duration", 0.0))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Duração inválida detectada por ffprobe: {format_info}") from exc

    if duration_s <= 0:
        raise ValueError(f"Duração de vídeo inválida (<=0): {duration_s}")

    return {
        "codec": codec,
        "duration_s": duration_s
    }


def calculate_video_hash(file_path: Path) -> str:
    """Calcula SHA-256 do arquivo gerado."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def process_motion_handoff(
    input_path: Path,
    output_handoff_path: Path,
    output_video_path: Path | None = None
) -> Path:
    """Executa a extração de dados do roteiro, render via Remotion e selagem do handoff."""
    if not check_doctor():
        raise RuntimeError("Ambiente inválido para execução de remotion_motion.")

    logger.info("Abrindo handoff de roteiro: %s", input_path)
    valido, motivo, body = abrir_handoff(input_path)
    if not valido:
        raise RuntimeError(f"Falha ao validar handoff de entrada: {motivo}")

    title = body.get("title", "Ouroboros Motion")
    subtitle = body.get("subtitle", "Geração Automática")
    cenas = body.get("cenas", [])

    fps = 60
    # Calcula total de frames com base nas cenas ou duração padrão
    if cenas and isinstance(cenas, list):
        duracao_total_s = sum(float(c.get("duracao_s", 2.0)) for c in cenas)
    else:
        duracao_total_s = float(body.get("duration_s", 2.0))

    if duracao_total_s <= 0:
        duracao_total_s = 2.0

    total_frames = max(60, int(duracao_total_s * fps))

    # Resolve caminhos de saída
    output_handoff_path = output_handoff_path.resolve()
    output_handoff_path.parent.mkdir(parents=True, exist_ok=True)

    if output_video_path is None:
        video_out = output_handoff_path.with_suffix(".mp4")
    else:
        video_out = output_video_path.resolve()
    video_out.parent.mkdir(parents=True, exist_ok=True)

    props_payload = {
        "title": title,
        "subtitle": subtitle
    }

    runner_cmd = get_remotion_runner()
    entry_point = "src/index.ts"
    composition_id = "Main"

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp_props:
        json.dump(props_payload, tmp_props, ensure_ascii=False)
        tmp_props_path = Path(tmp_props.name).resolve()

    try:
        render_cmd = runner_cmd + [
            "render",
            entry_point,
            composition_id,
            str(video_out),
            "--props", str(tmp_props_path),
            "--frames", f"0-{total_frames - 1}",
            "--codec", "h264"
        ]

        logger.info("Disparando Remotion CLI: %s", " ".join(render_cmd))
        result = subprocess.run(
            render_cmd,
            cwd=str(REMOTION_ENGINE_DIR),
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Remotion render falhou (exit {result.returncode}):\n{result.stderr.strip()}\n{result.stdout.strip()}"
            )

        # Validação ffprobe
        probe_data = validate_video_with_ffprobe(video_out)
        video_hash = calculate_video_hash(video_out)

        out_body = {
            "video_path": str(video_out),
            "video_sha256": video_hash,
            "codec": probe_data["codec"],
            "duration_s": probe_data["duration_s"],
            "fps": fps,
            "resolution": [1920, 1080],
            "total_frames": total_frames,
            "source_script_handoff": str(input_path.resolve())
        }

        selar_handoff(
            dados=out_body,
            destino=output_handoff_path
        )
        logger.info("[+] Render concluído e handoff selado com sucesso: %s", output_handoff_path)
        return video_out

    finally:
        if tmp_props_path.exists():
            try:
                os.remove(tmp_props_path)
            except OSError as cleanup_err:
                logger.warning("Falha ao remover arquivo de props temporário: %s", cleanup_err)


def main():
    parser = argparse.ArgumentParser(description="Renderizador real Remotion para pipelines AIDD.")
    parser.add_argument("--doctor", action="store_true", help="Diagnóstico de ambiente")
    parser.add_argument("--input", type=Path, help="Handoff de roteiro de entrada")
    parser.add_argument("--output-handoff", type=Path, help="Handoff de saída com assets de motion")
    parser.add_argument("--output-video", type=Path, default=None, help="Caminho do arquivo .mp4 resultante")
    args = parser.parse_args()

    if args.doctor:
        healthy = check_doctor()
        sys.exit(0 if healthy else 1)

    if args.input and args.output_handoff:
        try:
            process_motion_handoff(args.input, args.output_handoff, args.output_video)
            sys.exit(0)
        except Exception as exc:
            logger.error("Erro no processamento de motion: %s", exc)
            sys.exit(1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
