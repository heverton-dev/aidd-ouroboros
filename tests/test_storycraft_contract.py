"""
test_storycraft_contract.py — Testes de contrato e determinismo do dark_storycraft.py (NT-11)
"""

import hashlib
import json
import sys
from pathlib import Path
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_SKILL_SCRIPTS = _REPO_ROOT / "aidd-skills" / "aidd-craft-story-ptbr" / "scripts"
if str(_SKILL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SKILL_SCRIPTS))

from motores.governanca.handoff_crypto import selar_handoff, abrir_handoff

from dark_storycraft import (
    extract_script_parameters,
    build_prompt,
    validate_roteiro,
    transcreate_to_dark_script,
)


@pytest.fixture
def handoff_a(tmp_path: Path) -> Path:
    arquivo = tmp_path / "handoff_a.json"
    dados = {
        "$schema": "https://aidd.framework/schemas/handoff-v1.json",
        "producer_skill": "aidd-rea-video-youtube",
        "producer_version": "1.0.0",
        "status": "SUCCESS",
        "artifacts": {},
        "domain_data": {
            "title": "Google Flow Tutorial Completo",
            "hook_original": "Aprenda a animar roteiros em 5 minutos.",
            "ritmo": "rapido",
            "duracao_estimada_s": 120.0,
            "topicos": ["Setup", "Roteiro", "Animacao", "Export"],
        },
    }
    selar_handoff(dados, chave="test-secret", destino=arquivo)
    return arquivo


@pytest.fixture
def handoff_b(tmp_path: Path) -> Path:
    arquivo = tmp_path / "handoff_b.json"
    dados = {
        "$schema": "https://aidd.framework/schemas/handoff-v1.json",
        "producer_skill": "aidd-rea-video-youtube",
        "producer_version": "1.0.0",
        "status": "SUCCESS",
        "artifacts": {},
        "domain_data": {
            "title": "DeepSeek R1 para Devs",
            "hook_original": "Descubra como o novo modelo pensa.",
            "ritmo": "analitico",
            "duracao_estimada_s": 240.0,
            "topicos": ["Introducao", "Arquitetura", "Benchmarks", "Conclusao"],
        },
    }
    selar_handoff(dados, chave="test-secret", destino=arquivo)
    return arquivo


@pytest.fixture
def valid_roteiro_fixture(tmp_path: Path) -> Path:
    fixture_path = tmp_path / "valid_roteiro.json"
    conteudo = {
        "version": "1.0.0",
        "canal_target": "Dark Tech Brasil",
        "avatar": {
            "nome": "TechAvatar",
            "idioma": "pt-BR",
            "tom_de_voz": "dinamico e seguro",
        },
        "titulo_ptbr": "Dominando Animacoes com IA no YouTube",
        "hook_retencao_15s": "Se voce quer automatizar seu canal dark, este video e para voce nos primeiros 15 segundos.",
        "scenes": [
            {
                "scene_id": "cena-01",
                "tipo": "AVATAR_TELA_CHEIA",
                "duracao_estimada_s": 15.0,
                "fala_avatar": "Ola desenvolvedores, bem-vindos ao canal.",
                "diretivas_visuais": "Avatar centralizado em estudio escuro.",
            },
            {
                "scene_id": "cena-02",
                "tipo": "ANIMACAO_REMOTION",
                "duracao_estimada_s": 25.0,
                "fala_avatar": "Aqui mostramos a arquitetura do pipeline.",
                "diretivas_visuais": "Graficos cineticos aparecendo da esquerda.",
            },
        ],
    }
    fixture_path.write_text(json.dumps(conteudo, ensure_ascii=False), encoding="utf-8")
    return fixture_path


@pytest.fixture
def invalid_placeholder_fixture(tmp_path: Path) -> Path:
    fixture_path = tmp_path / "invalid_placeholder.json"
    conteudo = {
        "version": "1.0.0",
        "canal_target": "Dark Tech Brasil",
        "avatar": {
            "nome": "TechAvatar",
            "idioma": "pt-BR",
            "tom_de_voz": "dinamico",
        },
        "titulo_ptbr": "Dominando Animacoes com IA",
        "hook_retencao_15s": "Aguarde enquanto carregamos TODO os detalhes...",
        "scenes": [
            {
                "scene_id": "cena-01",
                "tipo": "AVATAR_TELA_CHEIA",
                "duracao_estimada_s": 15.0,
                "fala_avatar": "Texto com [PREENCHER] pendente.",
            }
        ],
    }
    fixture_path.write_text(json.dumps(conteudo, ensure_ascii=False), encoding="utf-8")
    return fixture_path


def test_prompts_have_different_hashes_for_different_inputs(handoff_a: Path, handoff_b: Path):
    params_a = extract_script_parameters(handoff_a, segredo=b"test-secret")
    params_b = extract_script_parameters(handoff_b, segredo=b"test-secret")

    prompt_a = build_prompt(params_a)
    prompt_b = build_prompt(params_b)

    hash_a = hashlib.sha256(prompt_a.encode("utf-8")).hexdigest()
    hash_b = hashlib.sha256(prompt_b.encode("utf-8")).hexdigest()

    assert hash_a != hash_b
    assert params_a["title"] in prompt_a
    assert params_b["title"] in prompt_b


def test_validation_rejects_placeholders_and_invalid_schema(invalid_placeholder_fixture: Path):
    dados = json.loads(invalid_placeholder_fixture.read_text(encoding="utf-8"))
    valido, erros = validate_roteiro(dados)
    assert not valido
    assert any("placeholder" in str(e).lower() for e in erros)


def test_validation_approves_valid_fixture(valid_roteiro_fixture: Path):
    dados = json.loads(valid_roteiro_fixture.read_text(encoding="utf-8"))
    valido, erros = validate_roteiro(dados)
    assert valido
    assert erros == []


def test_offline_mode_emits_partial_handoff_and_saves_prompt(handoff_a: Path, tmp_path: Path):
    out_handoff = tmp_path / "out_handoff.json"
    result = transcreate_to_dark_script(
        upstream_handoff_path=handoff_a,
        output_file=out_handoff,
        offline=True,
        segredo=b"test-secret",
    )

    assert result["status"] == "PARTIAL"
    valido, motivo, envelope = abrir_handoff(out_handoff, chave="test-secret")
    assert valido
    assert envelope["status"] == "PARTIAL"
    assert "prompt_artefato" in envelope["artifacts"]
    prompt_path = Path(envelope["artifacts"]["prompt_artefato"])
    assert prompt_path.exists()
    assert len(prompt_path.read_text(encoding="utf-8")) > 50


def test_full_pipeline_with_valid_fixture(handoff_a: Path, valid_roteiro_fixture: Path, tmp_path: Path):
    out_handoff = tmp_path / "out_handoff_success.json"
    result = transcreate_to_dark_script(
        upstream_handoff_path=handoff_a,
        output_file=out_handoff,
        llm_fixture_path=valid_roteiro_fixture,
        offline=False,
        segredo=b"test-secret",
    )

    assert result["status"] == "SUCCESS"
    valido, motivo, envelope = abrir_handoff(out_handoff, chave="test-secret")
    assert valido
    assert envelope["status"] == "SUCCESS"
    assert envelope["domain_data"]["titulo_ptbr"] == "Dominando Animacoes com IA no YouTube"
