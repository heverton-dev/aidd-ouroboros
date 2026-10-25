import json
import subprocess
import sys
from pathlib import Path
import pytest
import jsonschema

from ouroboros import sintetizar_plano


def test_sintetizar_plano_apk_valido():
    target = "meu_app.apk"
    goal = "Engenharia reversa profunda e extração de rotas"
    plano = sintetizar_plano(target=target, goal=goal)

    assert plano["target"] == target
    assert plano["goal"] == goal
    assert plano["deterministic"] is True
    assert len(plano["steps"]) >= 1
    assert plano["steps"][0]["skill"] == "aidd-rea-app-android"
    assert plano["steps"][0]["input_type"] in ["file/apk", "application/vnd.android.package-archive"]


def test_sintetizar_plano_zip_apk_valido():
    target = "pacote_app.zip"
    goal = "Desmontagem estática e análise de segurança de APK"
    plano = sintetizar_plano(target=target, goal=goal)

    assert plano["target"] == target
    assert plano["deterministic"] is True
    assert len(plano["steps"]) >= 1
    assert plano["steps"][0]["skill"] == "aidd-rea-app-android"


def test_sintetizar_plano_valida_contra_schema():
    target = "exemplo.apk"
    goal = "Extrair componentes e fluxo de navegação"
    plano = sintetizar_plano(target=target, goal=goal)

    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "PLAN.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Não deve levantar jsonschema.ValidationError
    jsonschema.validate(instance=plano, schema=schema)


def test_sintetizar_plano_target_desconhecido():
    with pytest.raises(ValueError, match="Não foi possível mapear"):
        sintetizar_plano(target="arquivo.xyz_inexistente", goal="Qualquer objetivo")


def test_cli_ouroboros_dry_run_plan(tmp_path):
    root_dir = Path(__file__).resolve().parent.parent
    ouroboros_py = root_dir / "ouroboros.py"

    cmd = [
        sys.executable,
        str(ouroboros_py),
        "--target",
        "app_alvo.apk",
        "--goal",
        "Mapeamento de rotas e segurança",
        "--dry-run"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root_dir))
    assert res.returncode == 0
    dados = json.loads(res.stdout)
    assert dados["deterministic"] is True
    assert dados["steps"][0]["skill"] == "aidd-rea-app-android"


def test_cli_ouroboros_output_plan_file(tmp_path):
    root_dir = Path(__file__).resolve().parent.parent
    ouroboros_py = root_dir / "ouroboros.py"
    output_file = tmp_path / "custom_plan.json"

    cmd = [
        sys.executable,
        str(ouroboros_py),
        "--target",
        "app_alvo.apk",
        "--goal",
        "Engenharia reversa",
        "--dry-run",
        "--output-plan",
        str(output_file)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root_dir))
    assert res.returncode == 0
    assert output_file.exists()
    conteudo = json.loads(output_file.read_text(encoding="utf-8"))
    assert conteudo["target"] == "app_alvo.apk"
    assert conteudo["steps"][0]["skill"] == "aidd-rea-app-android"
