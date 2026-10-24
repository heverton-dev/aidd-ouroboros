"""
Teste automatizado para o Pipeline Híbrido de Stitching Playwright + Remotion via FFmpeg (TK-04).
"""

from pathlib import Path
import tempfile
import unittest

# Importa as funções estendidas no pipeline de compose
from scripts.hybrid_stitch import (
    build_remotion_render_command,
    detect_scene_engine,
    generate_ffmpeg_concat_file,
)


class TestHybridStitch(unittest.TestCase):
    def test_detect_scene_engine_remotion(self):
        """Valida a detecção de cenas animadas com motor Remotion."""
        scene_remotion = {
            "id": "cena-01-intro",
            "layout": "animacao_conceitual",
            "engine": "remotion",
            "narration": "Conceito fundamental",
        }
        self.assertEqual(detect_scene_engine(scene_remotion), "remotion")

        scene_layout_only = {
            "id": "cena-02-diagram",
            "layout": "animacao_conceitual",
        }
        self.assertEqual(detect_scene_engine(scene_layout_only), "remotion")

    def test_detect_scene_engine_default(self):
        """Cenas de tela normais devem ser tratadas pelo motor padrão (playwright/screen)."""
        scene_app = {
            "id": "cena-03-app",
            "layout": "app",
            "steps": ["step-01"],
        }
        self.assertEqual(detect_scene_engine(scene_app), "playwright")

    def test_build_remotion_render_command(self):
        """Valida que o comando montado para render do Remotion é determinístico."""
        cmd = build_remotion_render_command(
            entry_point=Path("motores/remotion/src/index.ts"),
            composition_id="Main",
            out_file=Path("out/cena-01.mp4"),
            fps=60,
        )
        cmd_str = " ".join(cmd)
        self.assertIn("remotion", cmd_str)
        self.assertIn("render", cmd_str)
        self.assertIn("Main", cmd_str)
        self.assertIn("cena-01.mp4", cmd_str)
        self.assertIn("--fps 60", cmd_str)

    def test_generate_ffmpeg_concat_file(self):
        """Valida a geração da lista de concatenação demuxer do FFmpeg."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            videos = [
                tmp_path / "scene-01.mp4",
                tmp_path / "scene-02.mp4",
            ]
            concat_txt = tmp_path / "concat.txt"
            generate_ffmpeg_concat_file(videos, concat_txt)

            self.assertTrue(concat_txt.exists())
            content = concat_txt.read_text(encoding="utf-8")
            self.assertIn("file 'scene-01.mp4'", content)
            self.assertIn("file 'scene-02.mp4'", content)


if __name__ == "__main__":
    unittest.main()
