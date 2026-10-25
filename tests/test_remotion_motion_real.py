"""
Testes reais e determinísticos para remotion_motion.py (NT-10)
Valida --doctor, render real Remotion e inspeção ffprobe do .mp4.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
import pytest

from motores.governanca.handoff_crypto import selar_handoff, abrir_handoff

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = PROJECT_ROOT / "aidd-skills" / "aidd-motion-remotion-core" / "scripts" / "remotion_motion.py"

@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    monkeypatch.setenv("AIDD_HANDOFF_KEY", "test_key_secret_ouroboros_v2_32bytes")

def test_doctor_passes_when_prerequisites_met():
    """--doctor deve retornar 0 no ambiente com bun/npx, ffprobe e node_modules."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--doctor"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    assert result.returncode == 0
    assert "[OK]" in (result.stdout + result.stderr) or "[+]" in (result.stdout + result.stderr)

def test_doctor_fails_closed_when_tools_missing(monkeypatch):
    """Doctor deve falhar se ffprobe ou remotion engine estiverem ausentes."""
    # Modifica PATH para simular ausência de ferramentas
    env_sem_tools = os.environ.copy()
    env_sem_tools["PATH"] = ""
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--doctor"],
        capture_output=True,
        text=True,
        env=env_sem_tools,
        cwd=str(PROJECT_ROOT)
    )
    assert result.returncode != 0

def test_remotion_render_real_flow(tmp_path):
    """Executa renderização real do Remotion com handoff selado e validação ffprobe."""
    if not shutil.which("ffprobe") or not shutil.which("bun") and not shutil.which("npx"):
        pytest.skip("Binários bun/npx ou ffprobe não disponíveis para render.")

    # 1. Cria roteiro de entrada selado
    roteiro_input = tmp_path / "roteiro_handoff.json"
    body_roteiro = {
        "title": "Vídeo Teste Ouroboros",
        "subtitle": "Render Determinístico Remotion",
        "cenas": [
            {"id": "cena_1", "titulo": "Intro", "duracao_s": 1},
            {"id": "cena_2", "titulo": "Conceito", "duracao_s": 1}
        ]
    }
    selar_handoff(
        dados=body_roteiro,
        destino=roteiro_input
    )

    # 2. Executa remotion_motion.py
    out_handoff = tmp_path / "motion_handoff.json"
    out_video = tmp_path / "output_motion.mp4"

    cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--input", str(roteiro_input),
        "--output-handoff", str(out_handoff),
        "--output-video", str(out_video)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    assert result.returncode == 0, f"Falha na renderização: {result.stderr}\nStdout: {result.stdout}"

    # 3. Validações do vídeo gerado
    assert out_video.exists(), "Arquivo .mp4 não foi gerado no disco"
    assert out_video.stat().st_size > 1000, "Arquivo .mp4 parece vazio ou corrompido"

    # 4. Valida handoff de saída
    assert out_handoff.exists()
    valido, motivo, body = abrir_handoff(out_handoff)
    assert valido is True, f"Handoff inválido: {motivo}"
    assert body["video_path"] == str(out_video)
    assert body["codec"] == "h264"
    assert body["duration_s"] > 0
