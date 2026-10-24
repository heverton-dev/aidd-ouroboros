"""
Teste automatizado para os Modos de Análise (Conteúdo vs Estrutura) e Thumbnail OCR (aidd-rea-video-youtube).
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

# Adicionar aidd-rea-video-youtube ao path
REENGINEER_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-rea-video-youtube" / "scripts"
sys.path.insert(0, str(REENGINEER_SCRIPTS))

from video_reengineer import (
    generate_conteudo_tecnico,
    generate_estrutura_narrativa,
)


class TestVideoReengineerModes(unittest.TestCase):
    def test_generate_conteudo_tecnico(self):
        """Valida a geração de conteudo_tecnico.md com evidências REA."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            info = {
                "title": "Tutorial Teste Remotion",
                "channel": "Tester",
                "duration": 120,
                "webpage_url": "https://youtube.com/watch?v=123",
            }
            prompts_file = tmp_path / "prompts.txt"
            prompts_file.write_text("npm i remotion\nuseCurrentFrame()\n", encoding="utf-8")
            tsv_file = tmp_path / "transcript.tsv"
            tsv_file.write_text("start\tend\tts\ttext\n0\t5\t[00:00]\tInicio\n", encoding="utf-8")

            out_file = generate_conteudo_tecnico(tmp_path, info, prompts_file, tsv_file)
            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("Engenharia Reversa de Conteúdo Técnico", content)
            self.assertIn("Remotion", content)
            self.assertIn("[OBSERVADO NO FRAME]", content)

    def test_generate_estrutura_narrativa(self):
        """Valida a geração de estrutura_narrativa.md com Hook, Thumbnail OCR e Descrição."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            visual_dir = tmp_path / "visual"
            visual_dir.mkdir(parents=True, exist_ok=True)

            thumb_ocr = visual_dir / "thumbnail_ocr.txt"
            thumb_ocr.write_text("TEXTO DA CAPA 10X", encoding="utf-8")

            info = {
                "title": "Como fazer animações virarem tutoriais",
                "description": "00:00 Intro\n01:00 Setup\nLinks e cupom KAV",
                "tags": ["remotion", "kav"],
                "duration": 100,
            }
            tsv_file = tmp_path / "transcript.tsv"
            tsv_file.write_text(
                "start_s\tend_s\ttimestamp\ttext\n"
                "0.0\t8.0\t[00:00]\tSe tem um pedido que sempre recebo e como faco animacoes.\n"
                "80.0\t95.0\t[01:20]\tObrigado por assistir se inscreva no canal.\n",
                encoding="utf-8",
            )

            out_file = generate_estrutura_narrativa(tmp_path, info, tsv_file, visual_dir)
            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("Engenharia Reversa de Estrutura Narrativa", content)
            self.assertIn("TEXTO DA CAPA 10X", content)
            self.assertIn("Anatomia do Hook de Retenção", content)
            self.assertIn("Se tem um pedido que sempre recebo", content)
            self.assertIn("Obrigado por assistir", content)


if __name__ == "__main__":
    unittest.main()
