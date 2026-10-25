import subprocess
import sys
import json
import pytest
from pathlib import Path

PYTHON_EXE = sys.executable
BASE_DIR = Path(__file__).resolve().parent.parent

APP_REENGINEER = BASE_DIR / "aidd-skills" / "aidd-rea-app-android" / "scripts" / "app_reengineer.py"
SOCIAL_REENGINEER = BASE_DIR / "aidd-skills" / "aidd-rea-social-carousel" / "scripts" / "social_reengineer.py"
VIDEO_MATERIALIZER = BASE_DIR / "aidd-skills" / "aidd-materialize-video-synth" / "scripts" / "video_materializer.py"

FORBIDDEN_STRINGS = [
    "api.app.com",
    "LoginActivity",
    "Como automatizar agentes com IA sem codigo",
    "Storyboard Studio (Remotion",
]

def test_no_forbidden_mock_strings_in_scripts():
    """Garante que dados falsos inventados foram expurgados dos scripts."""
    scripts = [APP_REENGINEER, SOCIAL_REENGINEER, VIDEO_MATERIALIZER]
    for script in scripts:
        content = script.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_STRINGS:
            assert forbidden not in content, f"String proibida '{forbidden}' encontrada em {script.name}"

def test_app_reengineer_non_apk_returns_empty_and_partial(tmp_path):
    """Arquivo nao-apk deve retornar permissions vazio e status PARTIAL com degraded_reasons."""
    dummy_file = tmp_path / "not_an_apk.txt"
    dummy_file.write_text("isto nao e um apk", encoding="utf-8")
    out_dir = tmp_path / "out_android"

    cmd = [
        PYTHON_EXE,
        str(APP_REENGINEER),
        "--apk", str(dummy_file),
        "--output", str(out_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Falha na execucao: {res.stderr}"

    manifest_path = out_dir / "manifest.json"
    assert manifest_path.exists(), "manifest.json nao foi gerado"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    permissions = data.get("permissions", [])
    activities = data.get("activities", [])
    urls = data.get("api_endpoints", [])
    status = data.get("status")
    degraded_reasons = data.get("degraded_reasons", [])

    assert permissions == [], f"Esperava permissions vazio, recebeu: {permissions}"
    assert activities == [], f"Esperava activities vazio, recebeu: {activities}"
    assert urls == [], f"Esperava api_endpoints vazio, recebeu: {urls}"
    assert status == "PARTIAL", f"Esperava status PARTIAL, recebeu: {status}"
    assert len(degraded_reasons) > 0, "Esperava degraded_reasons preenchido"

def test_social_reengineer_empty_dir_returns_partial(tmp_path):
    """Diretorio sem imagens deve retornar slides_data vazia e status PARTIAL sem allow-placeholder."""
    empty_dir = tmp_path / "empty_social"
    empty_dir.mkdir()
    out_dir = tmp_path / "out_social"

    cmd = [
        PYTHON_EXE,
        str(SOCIAL_REENGINEER),
        "--input", str(empty_dir),
        "--output", str(out_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Falha na execucao: {res.stderr}"

    manifest_path = out_dir / "manifest.json"
    assert manifest_path.exists(), "manifest.json nao foi gerado"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    slides = data.get("slides", [])
    status = data.get("status")
    degraded_reasons = data.get("degraded_reasons", [])

    assert slides == [], f"Esperava slides vazio, recebeu: {slides}"
    assert status == "PARTIAL", f"Esperava status PARTIAL, recebeu: {status}"
    assert len(degraded_reasons) > 0, "Esperava degraded_reasons preenchido"

def test_video_materializer_fails_without_remotion_and_placeholder(tmp_path):
    """Sem Remotion/ffmpeg e sem --allow-placeholder, materializador deve falhar com exit code != 0."""
    script_file = tmp_path / "fake_script.json"
    script_file.write_text(json.dumps({"title": "Teste", "scenes": []}), encoding="utf-8")
    out_dir = tmp_path / "out_video"

    cmd = [
        PYTHON_EXE,
        str(VIDEO_MATERIALIZER),
        "--input", str(script_file),
        "--output", str(out_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    # Deve falhar com exit != 0 porque renderizacao real nao ocorreu e placeholder nao foi permitido
    assert res.returncode != 0, f"Esperava erro (exit != 0) sem allow-placeholder, mas retornou 0. stdout: {res.stdout}"
