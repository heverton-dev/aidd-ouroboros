"""
Teste automatizado para o Dissecador Social e de Carrosséis (aidd-rea-social-carousel).
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

SOCIAL_REENGINEER_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-rea-social-carousel" / "scripts"
sys.path.insert(0, str(SOCIAL_REENGINEER_SCRIPTS))

from social_reengineer import dissect_social_carousel


class TestSocialReengineer(unittest.TestCase):
    def test_dissect_social_carousel_from_folder(self):
        """Valida que a dissecação de carrossel emite artefatos REA completos e envelope HANDOFF.json."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_slides = Path(tmp_dir) / "slides_input"
            input_slides.mkdir()
            # Criar 3 slides de teste
            (input_slides / "slide_01.jpg").write_text("Hook: 3 segredos que ninguem te conta sobre IA", encoding="utf-8")
            (input_slides / "slide_02.jpg").write_text("Passo 1: Crie pipelines deterministiscos", encoding="utf-8")
            (input_slides / "slide_03.jpg").write_text("CTA: Comente LEGO para acessar", encoding="utf-8")

            out_dir = Path(tmp_dir) / "output_dissection"
            custom_handoff = Path(tmp_dir) / "handoff.json"

            dissect_social_carousel(
                input_source=str(input_slides),
                output_dir=out_dir,
                output_handoff=custom_handoff
            )

            self.assertTrue((out_dir / "tokens" / "TOKENS_DESIGN.json").exists())
            self.assertTrue((out_dir / "conteudo_tecnico.md").exists())
            self.assertTrue((out_dir / "estrutura_narrativa.md").exists())
            self.assertTrue((out_dir / "MANIFEST_REA.json").exists())
            self.assertTrue(custom_handoff.exists())

            # Validar estrutura do envelope de handoff
            handoff_data = json.loads(custom_handoff.read_text(encoding="utf-8"))
            self.assertEqual(handoff_data["producer_skill"], "aidd-rea-social-carousel")
            self.assertEqual(handoff_data["status"], "SUCCESS")
            self.assertIn("tokens_design", handoff_data["artifacts"])
            self.assertIn("estrutura_narrativa", handoff_data["artifacts"])


if __name__ == "__main__":
    unittest.main()
