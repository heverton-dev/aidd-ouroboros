"""
Teste automatizado para os Presets de Spring Physics e Componentes de Diagrama (TK-02).
"""

from pathlib import Path
import re
import unittest


class TestRemotionPhysics(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).parent.parent
        self.remotion_src = self.root_dir / "motores" / "remotion" / "src"
        self.physics_file = self.remotion_src / "theme" / "physics.ts"
        self.node_card_file = self.remotion_src / "components" / "NodeCard.tsx"
        self.connecting_line_file = self.remotion_src / "components" / "ConnectingLine.tsx"

    def test_files_exist(self):
        """Valida que todos os arquivos do módulo de física e componentes existem."""
        self.assertTrue(self.physics_file.exists(), f"Arquivo ausente: {self.physics_file}")
        self.assertTrue(self.node_card_file.exists(), f"Arquivo ausente: {self.node_card_file}")
        self.assertTrue(self.connecting_line_file.exists(), f"Arquivo ausente: {self.connecting_line_file}")

    def test_physics_presets_exported(self):
        """Valida se springPresets exporta snappy, smooth e bouncy com parâmetros válidos."""
        self.assertTrue(self.physics_file.exists())
        content = self.physics_file.read_text(encoding="utf-8")

        self.assertIn("export const springPresets", content)
        self.assertIn("snappy", content)
        self.assertIn("smooth", content)
        self.assertIn("bouncy", content)

        # Checa ausência de NaN ou divisões por zero óbvias
        self.assertNotIn("NaN", content)
        self.assertNotIn("Infinity", content)

    def test_connecting_line_svg_interpolation(self):
        """Valida se ConnectingLine renderiza SVG e usa interpolação de caminho curvo."""
        self.assertTrue(self.connecting_line_file.exists())
        content = self.connecting_line_file.read_text(encoding="utf-8")

        self.assertIn("<svg", content)
        self.assertIn("<path", content)
        self.assertIn("interpolate", content)

    def test_node_card_uses_spring(self):
        """Valida se NodeCard consome a física de mola."""
        self.assertTrue(self.node_card_file.exists())
        content = self.node_card_file.read_text(encoding="utf-8")

        self.assertIn("spring", content)
        self.assertIn("springPresets", content)


if __name__ == "__main__":
    unittest.main()
