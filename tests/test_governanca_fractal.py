# -*- coding: utf-8 -*-
"""
test_governanca_fractal.py — Testes Unitários dos Quality Gates Fractais e Integridade Criptográfica
Padrão: AIDD Universal Architecture / Zero Stubs / Zero Mocks / Token Economy
"""

import ast
import json
from pathlib import Path
import pytest
import sys
import tempfile

# Injetar raiz da branch no sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from motores.governanca.gate_ast import scan_path, scan_file
from motores.governanca.handoff_crypto import (
    criar_envelope_handoff,
    verificar_envelope_handoff,
    calcular_sha256_arquivo,
    calcular_hmac_dict
)
from motores.governanca.audit_runner import (
    auditar_micro_frontmatter,
    auditar_agents_governance
)


def test_gate_ast_detecta_stubs_e_aprova_codigo_real():
    """Valida que funções com 'pass', '...' ou 'NotImplementedError' falham, e código real passa."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Código com stub 'pass'
        bad_pass = tmp_path / "bad_pass.py"
        bad_pass.write_text("def operacao():\n    pass\n", encoding="utf-8")
        errs_pass = scan_file(bad_pass)
        assert len(errs_pass) == 1
        assert "Stub Proibido" in errs_pass[0]

        # 2. Código com stub '...'
        bad_elipse = tmp_path / "bad_elipse.py"
        bad_elipse.write_text("def operacao():\n    ...\n", encoding="utf-8")
        errs_elipse = scan_file(bad_elipse)
        assert len(errs_elipse) == 1
        assert "Stub Proibido" in errs_elipse[0]

        # 3. Código com 'NotImplementedError'
        bad_raise = tmp_path / "bad_raise.py"
        bad_raise.write_text("def operacao():\n    raise NotImplementedError('em breve')\n", encoding="utf-8")
        errs_raise = scan_file(bad_raise)
        assert len(errs_raise) == 1
        assert "Stub Proibido" in errs_raise[0]

        # 4. Código funcional legítimo (deve passar 100%)
        good_code = tmp_path / "good.py"
        good_code.write_text("def somar(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
        errs_good = scan_file(good_code)
        assert len(errs_good) == 0


def test_handoff_crypto_autenticidade_e_deteccao_de_adulteracao():
    """Testa criação de envelope HMAC-SHA256, verificação legítima e detecção de tampering."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # Criar artefato no disco
        asset_file = tmp_path / "video_spec.json"
        asset_file.write_text('{"video_id": "abc1234", "fps": 60}', encoding="utf-8")

        envelope_path = tmp_path / "HANDOFF.json"
        envelope = criar_envelope_handoff(
            origem_skill="aidd-rea-video-youtube",
            status="SUCCESS",
            artefatos={"spec": asset_file},
            metadados={"tokens_estimados": 240},
            caminho_saida=envelope_path
        )

        assert envelope_path.is_file()
        assert "hmac_sha256" in envelope

        # 1. Verificação legítima
        ok, msg = verificar_envelope_handoff(envelope_path)
        assert ok is True
        assert "100% íntegro" in msg

        # 2. Detecção de adulteração do payload JSON
        envelope_corrompido = json.loads(envelope_path.read_text(encoding="utf-8"))
        envelope_corrompido["payload"]["domain_metadata"]["tokens_estimados"] = 999999
        envelope_path.write_text(json.dumps(envelope_corrompido), encoding="utf-8")

        ok_tamper, msg_tamper = verificar_envelope_handoff(envelope_path)
        assert ok_tamper is False
        assert "Violação de Integridade" in msg_tamper

        # 3. Detecção de adulteração no arquivo de disco apontado
        # Restaurar envelope correto
        criar_envelope_handoff(
            origem_skill="aidd-rea-video-youtube",
            status="SUCCESS",
            artefatos={"spec": asset_file},
            caminho_saida=envelope_path
        )
        # Adulterar o conteúdo do arquivo físico apontado
        asset_file.write_text('{"video_id": "MODIFICADO_SEM_PERMISSAO"}', encoding="utf-8")

        ok_disk, msg_disk = verificar_envelope_handoff(envelope_path)
        assert ok_disk is False
        assert "Adulteração no disco" in msg_disk


def test_conformidade_global_da_branch():
    """Garante que a branch feature-matt-penny atende integralmente a todos os gates."""
    root = Path(__file__).resolve().parent.parent

    # 1. Gate AST
    ast_res = scan_path(root)
    assert ast_res.passed, f"Gate AST falhou: {ast_res.errors}"

    # 2. Micro-Frontmatter (<= 25 palavras)
    mf_ok, mf_errs = auditar_micro_frontmatter(root)
    assert mf_ok, f"Gate Micro-Frontmatter falhou: {mf_errs}"

    # 3. AGENTS.md em todas as skills e pipelines (< 450 palavras)
    gov_ok, gov_errs = auditar_agents_governance(root)
    assert gov_ok, f"Gate AGENTS.md falhou: {gov_errs}"
