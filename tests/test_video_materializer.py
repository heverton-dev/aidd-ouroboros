"""
Teste automatizado para o Materializador Audiovisual (aidd-materialize-video-synth).
"""

from pathlib import Path
import sys
import tempfile
import unittest

# Adicionar aidd-materialize-video-synth ao path
MATERIALIZER_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-materialize-video-synth" / "scripts"
sys.path.insert(0, str(MATERIALIZER_SCRIPTS))

from video_materializer import (
    render_remotion_scene,
    synthesize_neural_voice,
)


class TestVideoMaterializer(unittest.TestCase):
    def test_synthesize_neural_voice(self):
        """Valida que a síntese de voz neural gera arquivo de áudio válido."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            out_audio = tmp_path / "voice_test.mp3"
            res = synthesize_neural_voice("Teste automatizado", out_audio)

            self.assertTrue(res.exists())
            self.assertGreater(res.stat().st_size, 0)

    def test_render_scene_generates_mp4(self):
        """Valida que a geração de cena audiovisual entrega um MP4 no disco."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            out_mp4 = tmp_path / "scene_test.mp4"
            res = render_remotion_scene(Path("non_existent"), out_mp4, fps=30)

            self.assertTrue(res.exists())
            self.assertGreater(res.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
