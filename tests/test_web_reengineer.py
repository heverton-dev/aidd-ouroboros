"""
Teste automatizado para o Dissecador Web e SaaS (aidd-rea-web-saas).
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

WEB_REENGINEER_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-rea-web-saas" / "scripts"
sys.path.insert(0, str(WEB_REENGINEER_SCRIPTS))

from web_reengineer import (
    extract_design_tokens,
    extract_tech_stack_and_routes,
    dissect_web_application,
)


class TestWebReengineer(unittest.TestCase):
    def test_extract_design_tokens(self):
        """Valida a extração de paleta de cores, tipografia e raios de borda a partir de CSS."""
        sample_html = """
        <html>
        <head>
            <style>
                body { background-color: #0B0F19; color: #F3F4F6; font-family: 'Geist', sans-serif; }
                .card { border-radius: 16px; background-color: #1E293B; }
                .btn { color: #6366F1; border-radius: 9999px; }
            </style>
        </head>
        <body><button>Clique Aqui</button></body>
        </html>
        """
        tokens = extract_design_tokens(sample_html)
        self.assertIn("colors", tokens)
        self.assertIn("typography", tokens)
        self.assertIn("border_radius", tokens)
        self.assertTrue(any("#0B0F19".lower() in c.lower() for c in tokens["colors"]["palette_detected"]))

    def test_extract_tech_stack_and_routes(self):
        """Valida que identifica Next.js/React, rotas internas e CTAs."""
        sample_html = """
        <html>
        <head><script id="__NEXT_DATA__">{}</script></head>
        <body>
            <a href="/login">Login</a>
            <a href="/dashboard">Dashboard</a>
            <a href="https://externo.com">Parceiro</a>
            <form action="/api/submit" method="POST"></form>
            <button>Criar Conta Grátis</button>
        </body>
        </html>
        """
        tech = extract_tech_stack_and_routes(sample_html, "https://meusaas.com")
        self.assertIn("Next.js", tech["stack_detected"])
        self.assertIn("/login", tech["internal_routes"])
        self.assertEqual(len(tech["forms_detected"]), 1)
        self.assertIn("Criar Conta Grátis", tech["ctas_detected"])

    def test_dissect_web_application_e2e(self):
        """Valida que a dissecação completa emite todos os artefatos REA e envelope HANDOFF.json."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "output_dissection"
            custom_handoff = Path(tmp_dir) / "custom_handoff.json"

            res_dir = dissect_web_application(
                url="https://exemplo-saas.com",
                output_dir=out_path,
                output_handoff=custom_handoff
            )

            self.assertTrue((out_path / "tokens" / "TOKENS_DESIGN.json").exists())
            self.assertTrue((out_path / "conteudo_tecnico.md").exists())
            self.assertTrue((out_path / "estrutura_ux.md").exists())
            self.assertTrue((out_path / "MANIFEST_REA.json").exists())
            self.assertTrue(custom_handoff.exists())

            # Validar estrutura do envelope de handoff
            handoff_data = json.loads(custom_handoff.read_text(encoding="utf-8"))
            # Formato canônico HMAC: corpo em body (espelhado em payload)
            body = handoff_data.get("body") or handoff_data
            self.assertEqual(body.get("producer_skill") or handoff_data.get("producer_skill"), "aidd-rea-web-saas")
            self.assertEqual(body.get("status"), "SUCCESS")
            artifacts = body.get("artifacts_pointers") or body.get("artifacts") or {}
            self.assertIn("tokens_design", artifacts)
            self.assertEqual(handoff_data.get("signature_algorithm"), "HMAC-SHA256")
            self.assertIn("seal", handoff_data)


if __name__ == "__main__":
    unittest.main()
