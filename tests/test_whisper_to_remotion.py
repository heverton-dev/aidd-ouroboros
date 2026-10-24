"""
Teste automatizado para o Conversor de Timestamps Whisper para Keyframes Remotion (TK-03).
"""

import json
from pathlib import Path
import tempfile
import unittest

from scripts.whisper_to_remotion import convert_whisper_tsv_to_remotion_props


class TestWhisperToRemotion(unittest.TestCase):
    def setUp(self):
        self.sample_tsv = (
            "start\tend\ttext\n"
            "0\t2500\tNeste tutorial vamos construir um pipeline autônomo.\n"
            "2500\t5000\tPrimeiro transcrevemos o áudio usando faster-whisper.\n"
            "5000\t8500\tEm seguida o Remotion gera as animações conceituais a 60 fps.\n"
        )

    def test_conversion_at_60_fps(self):
        """Valida que timestamps em ms são convertidos corretamente para frames a 60 fps."""
        with tempfile.NamedTemporaryFile("w+", suffix=".tsv", delete=False, encoding="utf-8") as f:
            f.write(self.sample_tsv)
            tsv_path = Path(f.name)

        try:
            props = convert_whisper_tsv_to_remotion_props(tsv_path, fps=60)

            self.assertEqual(props["fps"], 60)
            self.assertEqual(len(props["events"]), 3)

            # Evento 0: 0s -> 2.5s (0 -> 150 frames)
            ev0 = props["events"][0]
            self.assertEqual(ev0["startFrame"], 0)
            self.assertEqual(ev0["endFrame"], 150)
            self.assertEqual(ev0["durationInFrames"], 150)
            self.assertEqual(ev0["text"], "Neste tutorial vamos construir um pipeline autônomo.")

            # Evento 1: 2.5s -> 5.0s (150 -> 300 frames)
            ev1 = props["events"][1]
            self.assertEqual(ev1["startFrame"], 150)
            self.assertEqual(ev1["endFrame"], 300)

            # Evento 2: 5.0s -> 8.5s (300 -> 510 frames)
            ev2 = props["events"][2]
            self.assertEqual(ev2["startFrame"], 300)
            self.assertEqual(ev2["endFrame"], 510)

            # Duração total em frames
            self.assertEqual(props["totalDurationInFrames"], 510)
        finally:
            if tsv_path.exists():
                tsv_path.unlink()

    def test_conversion_at_30_fps(self):
        """Valida que o framerate configurável de 30 fps é respeitado."""
        with tempfile.NamedTemporaryFile("w+", suffix=".tsv", delete=False, encoding="utf-8") as f:
            f.write(self.sample_tsv)
            tsv_path = Path(f.name)

        try:
            props = convert_whisper_tsv_to_remotion_props(tsv_path, fps=30)
            self.assertEqual(props["fps"], 30)

            ev0 = props["events"][0]
            self.assertEqual(ev0["startFrame"], 0)
            self.assertEqual(ev0["endFrame"], 75)
            self.assertEqual(props["totalDurationInFrames"], 255)
        finally:
            if tsv_path.exists():
                tsv_path.unlink()


if __name__ == "__main__":
    unittest.main()
