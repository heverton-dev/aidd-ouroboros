"""
Testes TDD para NT-06: Entrypoint explícito e contrato CLI padrão nas 12 skills.
Valida:
1. Todas as 12 skills canônicas em aidd-skills/ possuem dependencies.json.
2. Cada dependencies.json define 'entrypoint' existente e 'cli_contract' com input_flag e output_flag.
3. Cada entrypoint suporta os argumentos definidos no contrato (--help e flags).
4. RUN_PIPELINE_TEMPLATE.py e pipelines existentes não usam globbing dinâmico para achar scripts de skill.
"""

import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "aidd-skills"
PIPELINES_DIR = ROOT / "aidd-pipelines"
TEMPLATE_PATH = ROOT / "aidd-skills" / "aidd-orchestrate-pipeline-creator" / "templates" / "RUN_PIPELINE_TEMPLATE.py"


def get_canonical_skills():
    tax_path = ROOT / "aidd-skills" / "TAXONOMY.json"
    with open(tax_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get("skills", {}).keys())


def test_all_12_skills_have_dependencies_json():
    skills = get_canonical_skills()
    assert len(skills) == 12
    for s in skills:
        dep_file = SKILLS_DIR / s / "dependencies.json"
        assert dep_file.is_file(), f"Skill {s} não possui dependencies.json"


def test_dependencies_json_schema_and_entrypoint_exists():
    skills = get_canonical_skills()
    for s in skills:
        dep_file = SKILLS_DIR / s / "dependencies.json"
        if not dep_file.is_file():
            pytest.fail(f"dependencies.json ausente em {s}")
        with open(dep_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        entrypoint = data.get("entrypoint")
        assert entrypoint, f"Skill {s} não define 'entrypoint' em dependencies.json"
        
        ep_path = SKILLS_DIR / s / entrypoint
        assert ep_path.is_file(), f"Entrypoint {entrypoint} de {s} não existe no disco"
        
        cli = data.get("cli_contract")
        assert isinstance(cli, dict), f"Skill {s} não define 'cli_contract' como dict em dependencies.json"
        assert "input_flag" in cli, f"Skill {s} sem 'input_flag' em cli_contract"
        assert "output_flag" in cli, f"Skill {s} sem 'output_flag' em cli_contract"


def test_entrypoints_cli_contract_executable():
    skills = get_canonical_skills()
    for s in skills:
        dep_file = SKILLS_DIR / s / "dependencies.json"
        if not dep_file.is_file():
            continue
        with open(dep_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        entrypoint = data.get("entrypoint")
        cli = data.get("cli_contract", {})
        if not entrypoint or not cli:
            continue
        
        ep_path = SKILLS_DIR / s / entrypoint
        if not ep_path.is_file():
            continue
            
        res = subprocess.run(
            [sys.executable, str(ep_path), "--help"],
            capture_output=True,
            text=True,
            cwd=str(SKILLS_DIR / s)
        )
        assert res.returncode == 0, f"Entrypoint {ep_path} falhou ao responder --help: {res.stderr}"
        help_out = res.stdout + res.stderr
        in_flag = cli.get("input_flag")
        out_flag = cli.get("output_flag")
        assert in_flag in help_out, f"Flag {in_flag} ausente no --help de {s} ({entrypoint})"
        assert out_flag in help_out, f"Flag {out_flag} ausente no --help de {s} ({entrypoint})"


def test_no_glob_in_pipeline_runners():
    files_to_check = []
    if TEMPLATE_PATH.is_file():
        files_to_check.append(TEMPLATE_PATH)
    
    if PIPELINES_DIR.is_dir():
        for runner in PIPELINES_DIR.glob("*/run_pipeline.py"):
            files_to_check.append(runner)
            
    for f in files_to_check:
        content = f.read_text(encoding="utf-8")
        assert 'glob("*.py")' not in content and "glob('*.py')" not in content, (
            f"Arquivo {f} ainda usa globbing dinâmico para encontrar scripts de skill"
        )
