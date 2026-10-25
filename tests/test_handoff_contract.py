"""Testes do contrato formalizado de handoff (body + seal) - NT-05 (C-02)."""
import json
import os
import pytest
from pathlib import Path
from motores.governanca.handoff_crypto import (
    selar,
    abrir,
    criar_envelope_handoff,
    verificar_envelope_handoff,
)


@pytest.fixture(autouse=True)
def setup_secret_key(monkeypatch):
    """Garante chave de teste em ambiente."""
    monkeypatch.setenv("OUROBOROS_HMAC_SECRET", "super-secret-test-key-for-nt05-ouroboros")


def test_selar_produz_estrutura_body_e_seal():
    dados = {
        "producer_skill": "skill-origem",
        "timestamp": "2026-10-25T12:00:00Z",
        "status": "GREEN",
        "artifacts_pointers": [],
        "domain_metadata": {"foo": "bar"},
    }
    envelope = selar(dados, key_id="ouroboros-v2")
    assert "body" in envelope
    assert "seal" in envelope
    assert envelope["body"] == dados
    assert envelope["seal"]["algorithm"] == "HMAC-SHA256"
    assert envelope["seal"]["key_id"] == "ouroboros-v2"
    assert "hmac_sha256" in envelope["seal"]
    assert "sealed_at" in envelope["seal"]


def test_abrir_valida_envelope_integro():
    dados = {
        "producer_skill": "skill-alpha",
        "status": "GREEN",
        "artifacts_pointers": [],
    }
    envelope = selar(dados)
    valido, motivo, corpo = abrir(envelope, verificar_disco=False)
    assert valido is True
    assert motivo == "OK"
    assert corpo == dados


def test_abrir_detecta_adulteracao_no_body():
    dados = {"status": "GREEN", "artifacts_pointers": []}
    envelope = selar(dados)
    envelope["body"]["status"] = "RED_TAMPERED"
    valido, motivo, corpo = abrir(envelope, verificar_disco=False)
    assert valido is False
    assert "HMAC" in motivo or "Assinatura" in motivo or "adulter" in motivo.lower()


def test_selar_protege_contra_reenvelope():
    dados = {"status": "GREEN"}
    envelope = selar(dados)
    # Tentar selar um envelope já selado deve falhar ou não aninhar body dentro de body
    with pytest.raises(ValueError, match="já selado|already sealed"):
        selar(envelope)


def test_retrocompatibilidade_envelope_legado_com_abrir():
    legado = {
        "envelope_format": "aidd_ouroboros_v1",
        "signature_algorithm": "HMAC-SHA256",
        "hmac_sha256": "fake-hash",
        "payload": {
            "producer_skill": "legacy-skill",
            "status": "GREEN",
            "artifacts_pointers": [],
        },
    }
    # Gerar HMAC real para o formato legado usando chave
    import hmac
    import hashlib
    key = b"super-secret-test-key-for-nt05-ouroboros"
    canon = json.dumps(legado["payload"], sort_keys=True, ensure_ascii=False).encode("utf-8")
    legado["hmac_sha256"] = hmac.new(key, canon, hashlib.sha256).hexdigest()

    valido, motivo, corpo = abrir(legado, verificar_disco=False)
    assert valido is True
    assert corpo == legado["payload"]


def test_criar_envelope_handoff_retorna_novo_formato_e_mantem_retrocompat():
    envelope = criar_envelope_handoff("skill-test", [], {"k": "v"})
    assert "body" in envelope
    assert "seal" in envelope
    valido, motivo = verificar_envelope_handoff(envelope, verificar_existencia_disco=False)
    assert valido is True
