"""Testes de seguranca e determinismo para handoff_crypto (NT-03)."""

import os
import subprocess
import sys
import pytest
from motores.governanca import handoff_crypto


def test_obter_chave_sem_env_e_sem_parametro(monkeypatch):
    monkeypatch.delenv("AIDD_HANDOFF_KEY", raising=False)
    monkeypatch.delenv("OUROBOROS_HMAC_SECRET", raising=False)
    with pytest.raises(RuntimeError) as exc_info:
        handoff_crypto.obter_chave()
    assert "AIDD_HANDOFF_KEY" in str(exc_info.value)


def test_obter_chave_com_env(monkeypatch):
    monkeypatch.setenv("AIDD_HANDOFF_KEY", "chave-secreta-env")
    assert handoff_crypto.obter_chave() == "chave-secreta-env"


def test_obter_chave_com_parametro_explicito(monkeypatch):
    monkeypatch.setenv("AIDD_HANDOFF_KEY", "chave-env")
    assert handoff_crypto.obter_chave("chave-parametro") == "chave-parametro"


def test_envelope_handoff_sucesso(monkeypatch):
    monkeypatch.setenv("AIDD_HANDOFF_KEY", "segredo-teste-123")
    payload = {"status": "ok", "artefatos": ["arquivo.txt"]}
    envelope = handoff_crypto.criar_envelope_handoff(
        origem_skill="skill-a",
        status="SUCCESS",
        metadados=payload
    )

    valido, msg = handoff_crypto.verificar_envelope_handoff(envelope)
    assert valido is True
    assert "100%" in msg.lower() or "sucesso" in msg.lower() or "autêntico" in msg.lower()


def test_envelope_handoff_payload_adulterado(monkeypatch):
    monkeypatch.setenv("AIDD_HANDOFF_KEY", "segredo-teste-123")
    payload = {"status": "ok", "contador": 1}
    envelope = handoff_crypto.criar_envelope_handoff(
        origem_skill="skill-a",
        status="SUCCESS",
        metadados=payload
    )

    envelope["payload"]["domain_metadata"]["contador"] = 2
    valido, msg = handoff_crypto.verificar_envelope_handoff(envelope)
    assert valido is False
    assert "violação de integridade" in msg.lower() or "adulterado" in msg.lower()


def test_envelope_handoff_sem_selo():
    envelope = {"envelope_format": "AIDD-CANONICAL-HANDOFF", "payload": {}}
    valido, msg = handoff_crypto.verificar_envelope_handoff(envelope, chave="chave")
    assert valido is False
    assert "incompleto" in msg.lower() or "ausente" in msg.lower()


def test_envelope_handoff_chave_divergente(monkeypatch):
    monkeypatch.setenv("AIDD_HANDOFF_KEY", "chave-correta")
    payload = {"dado": 42}
    envelope = handoff_crypto.criar_envelope_handoff(
        origem_skill="skill-a",
        status="SUCCESS",
        metadados=payload
    )

    valido, msg = handoff_crypto.verificar_envelope_handoff(envelope, chave="chave-errada")
    assert valido is False
    assert "adulterado" in msg.lower() or "não confere" in msg.lower()


def test_cli_sem_subcomando_retorna_exit_2(monkeypatch):
    monkeypatch.delenv("AIDD_HANDOFF_KEY", raising=False)
    proc = subprocess.run(
        [sys.executable, "-m", "motores.governanca.handoff_crypto"],
        capture_output=True,
        text=True
    )
    assert proc.returncode == 2
    assert "usage:" in proc.stderr.lower() or "utilitário" in proc.stderr.lower()
