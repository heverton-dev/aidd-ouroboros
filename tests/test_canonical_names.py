"""
Testes de nomes canônicos e resolução de taxonomia (NT-04).
"""
import glob
import json
import pytest
from pathlib import Path
from motores.governanca.taxonomy import resolve_skill_name, TAXONOMY_PATH

REPO_ROOT = Path(__file__).resolve().parent.parent

def test_pipeline_nodes_are_canonical():
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        tax = json.load(f)
    canonical_skills = set(tax.get("skills", {}).keys())

    pipeline_files = glob.glob(str(REPO_ROOT / "aidd-pipelines" / "*" / "PIPELINE.json"))
    assert len(pipeline_files) > 0, "Nenhum PIPELINE.json encontrado"

    invalid_nodes = []
    for p in pipeline_files:
        with open(p, "r", encoding="utf-8") as pf:
            data = json.load(pf)
        for node in data.get("nodes", []):
            skill = node.get("skill")
            if skill not in canonical_skills:
                invalid_nodes.append((Path(p).name, node.get("id"), skill))

    assert not invalid_nodes, f"Nós com skills não-canônicas encontrados: {invalid_nodes}"

def test_pipeline_creator_has_no_legacy_literals():
    creator_path = REPO_ROOT / "aidd-skills" / "aidd-orchestrate-pipeline-creator" / "scripts" / "pipeline_creator.py"
    assert creator_path.exists(), "pipeline_creator.py não encontrado"
    content = creator_path.read_text(encoding="utf-8")

    forbidden = [
        "aidd-video-reengineer",
        "aidd-skill-creator",
        "aidd-remotion-motion",
        "aidd-dark-storycraft",
        "aidd-video-materializer",
    ]
    found = [f'"{term}"' for term in forbidden if f'"{term}"' in content]
    assert not found, f"Literais legados encontrados em pipeline_creator.py: {found}"

def test_taxonomy_has_aliases_section():
    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        tax = json.load(f)
    assert "aliases" in tax, "Chave 'aliases' ausente em TAXONOMY.json"
    assert isinstance(tax["aliases"], dict), "'aliases' deve ser um dict"

def test_resolve_skill_name():
    # Canônica retorna direto
    assert resolve_skill_name("aidd-rea-video-youtube") == "aidd-rea-video-youtube"

    # Alias emite UserWarning e retorna canônico
    with pytest.warns(UserWarning, match="é um alias legado"):
        assert resolve_skill_name("aidd-video-reengineer") == "aidd-rea-video-youtube"

    # Desconhecido lança ValueError (fail-closed)
    with pytest.raises(ValueError, match="não consta na taxonomia oficial"):
        resolve_skill_name("skill-fantasma-inexistente")
