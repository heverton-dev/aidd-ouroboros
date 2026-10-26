"""
Teste automatizado para o Dissecador de Aplicativos Mobile e Binários (aidd-rea-app-android).
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

APP_REENGINEER_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-rea-app-android" / "scripts"
sys.path.insert(0, str(APP_REENGINEER_SCRIPTS))

from app_reengineer import scan_strings_and_urls, dissect_mobile_or_binary_app


class TestAppReengineer(unittest.TestCase):
    def test_scan_strings_and_urls(self):
        """Valida que extrai URLs, permissões Android e Activities de dados binários."""
        sample_bytes = b"Hello android.permission.CAMERA and android.permission.INTERNET with https://backend.app.com/api and MainActivity"
        urls, perms, activities = scan_strings_and_urls(sample_bytes)

        self.assertIn("https://backend.app.com/api", urls)
        self.assertIn("android.permission.CAMERA", perms)
        self.assertIn("android.permission.INTERNET", perms)
        self.assertIn("MainActivity", activities)

    def test_dissect_mobile_or_binary_app_e2e(self):
        """Valida a dissecação de um pacote APK simulado emitindo artefatos REA completos."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            apk_mock = tmp_path / "mock_app.apk"

            # Criar um APK zip mock com classes.dex e manifest
            with zipfile.ZipFile(apk_mock, "w") as z:
                z.writestr("AndroidManifest.xml", b"android.permission.ACCESS_FINE_LOCATION com.demo.app HomeActivity")
                z.writestr("classes.dex", b"https://api.demo.com/auth SettingsActivity FragmentView")

            out_dir = tmp_path / "output_dissection"
            custom_handoff = tmp_path / "handoff.json"

            dissect_mobile_or_binary_app(
                input_source=str(apk_mock),
                output_dir=out_dir,
                output_handoff=custom_handoff
            )

            self.assertTrue((out_dir / "tokens" / "TOKENS_DESIGN.json").exists())
            self.assertTrue((out_dir / "conteudo_tecnico.md").exists())
            self.assertTrue((out_dir / "arquitetura.md").exists())
            self.assertTrue((out_dir / "MANIFEST_REA.json").exists())
            self.assertTrue(custom_handoff.exists())

            # Validar estrutura do envelope
            handoff_data = json.loads(custom_handoff.read_text(encoding="utf-8"))
            body = handoff_data.get("body") or handoff_data
            self.assertEqual(body.get("producer_skill") or handoff_data.get("producer_skill"), "aidd-rea-app-android")
            self.assertEqual(body.get("status"), "SUCCESS")
            artifacts = body.get("artifacts_pointers") or body.get("artifacts") or {}
            self.assertIn("tokens_design", artifacts)
            self.assertIn("arquitetura", artifacts)
            self.assertEqual(handoff_data.get("signature_algorithm"), "HMAC-SHA256")
            self.assertIn("seal", handoff_data)


if __name__ == "__main__":
    unittest.main()
