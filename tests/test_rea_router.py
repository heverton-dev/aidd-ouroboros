"""
Teste automatizado para o Roteador Universal de Engenharia Reversa (aidd-rea-router).
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

REA_ROUTER_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-rea-router" / "scripts"
sys.path.insert(0, str(REA_ROUTER_SCRIPTS))

from rea_router import classify_target, route_and_execute


class TestReaRouter(unittest.TestCase):
    def test_classify_targets(self):
        """Valida que o roteador classifica com precisão os 4 tipos de mídia."""
        # 1. Vídeo
        res_vid = classify_target("https://www.youtube.com/watch?v=123456")
        self.assertEqual(res_vid["type"], "video")
        self.assertEqual(res_vid["skill"], "aidd-rea-video-youtube")

        # 2. Web App / SaaS
        res_web = classify_target("https://meu-saas.com/login")
        self.assertEqual(res_web["type"], "web")
        self.assertEqual(res_web["skill"], "aidd-rea-web-saas")

        # 3. Aplicativo / APK
        res_app = classify_target("bin/build/release.apk")
        self.assertEqual(res_app["type"], "app")
        self.assertEqual(res_app["skill"], "aidd-rea-app-android")

        # 4. Social (pasta com imagens de slides)
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_p = Path(tmp_dir)
            (tmp_p / "slide_01.png").write_text("fake image", encoding="utf-8")
            res_soc = classify_target(str(tmp_p))
            self.assertEqual(res_soc["type"], "social")
            self.assertEqual(res_soc["skill"], "aidd-rea-social-carousel")

    def test_route_and_execute_e2e(self):
        """Valida que o roteador despacha para o especialista web e emite HANDOFF.json."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "output_dissection"
            handoff_p = Path(tmp_dir) / "handoff.json"

            ok = route_and_execute(
                target="https://exemplo-roteamento.com",
                output_dir=out_dir,
                output_handoff=handoff_p
            )

            self.assertTrue(ok)
            self.assertTrue(handoff_p.exists())
            data = json.loads(handoff_p.read_text(encoding="utf-8"))
            self.assertEqual(data["producer_skill"], "aidd-rea-web-saas")
            self.assertEqual(data["status"], "SUCCESS")


if __name__ == "__main__":
    unittest.main()
