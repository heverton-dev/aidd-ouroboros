"""
Teste automatizado para o Scaffold do Motor Remotion (TK-01).
Valida a integridade estrutural, package.json, Root.tsx e diretrizes de IA.
"""

import json
from pathlib import Path
import unittest


class TestRemotionScaffold(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).parent.parent
        self.remotion_dir = self.root_dir / "motores" / "remotion"

    def test_directory_and_core_files_exist(self):
        """Verifica se os arquivos essenciais do scaffold Remotion existem."""
        expected_files = [
            self.remotion_dir / "package.json",
            self.remotion_dir / "src" / "index.ts",
            self.remotion_dir / "src" / "Root.tsx",
            self.remotion_dir / "skills" / "REMOTION_AI_GUIDELINES.md",
        ]
        for f in expected_files:
            self.assertTrue(f.exists(), f"Arquivo essencial ausente: {f}")

    def test_package_json_integrity(self):
        """Valida se o package.json possui as dependências e scripts canônicos do Remotion."""
        pkg_file = self.remotion_dir / "package.json"
        self.assertTrue(pkg_file.exists())
        with open(pkg_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Dependências essenciais
        deps = data.get("dependencies", {})
        dev_deps = data.get("devDependencies", {})
        all_deps = {**deps, **dev_deps}

        self.assertIn("remotion", all_deps, "remotion deve estar nas dependências")
        self.assertIn("@remotion/cli", all_deps, "@remotion/cli deve estar nas dependências")
        self.assertIn("react", all_deps, "react deve estar nas dependências")
        self.assertIn("react-dom", all_deps, "react-dom deve estar nas dependências")

        # Scripts
        scripts = data.get("scripts", {})
        self.assertIn("build", scripts, "Script 'build' deve estar configurado")
        self.assertIn("render", scripts, "Script 'render' deve estar configurado")

    def test_root_composition_spec(self):
        """Valida que Root.tsx define uma composição em 1080p a 60 fps."""
        root_tsx = self.remotion_dir / "src" / "Root.tsx"
        self.assertTrue(root_tsx.exists())
        content = root_tsx.read_text(encoding="utf-8")

        self.assertIn("Composition", content)
        self.assertIn("fps={60}", content)
        self.assertIn("width={1920}", content)
        self.assertIn("height={1080}", content)

    def test_ai_guidelines_present(self):
        """Valida que as diretrizes de assistência de IA estão documentadas."""
        guidelines_file = self.remotion_dir / "skills" / "REMOTION_AI_GUIDELINES.md"
        self.assertTrue(guidelines_file.exists())
        content = guidelines_file.read_text(encoding="utf-8")
        self.assertIn("Remotion", content)
        self.assertIn("spring", content)


if __name__ == "__main__":
    unittest.main()
