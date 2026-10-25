"""Configurações globais e fixtures para a suíte de testes do Ouroboros."""
import os
import pytest

@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Garante variáveis de ambiente necessárias para testes locais."""
    if "AIDD_HANDOFF_KEY" not in os.environ:
        monkeypatch.setenv("AIDD_HANDOFF_KEY", "test-ouroboros-v2-ci-key-hmac-sha256")
