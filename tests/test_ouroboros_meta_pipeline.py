"""
Teste automatizado para o Meta-Pipeline AIDD-OUROBOROS (Ciclo Infinito).
"""

import json
from pathlib import Path
import sys
import unittest

OUROBOROS_DIR = Path(__file__).parent.parent / "aidd-ouroboros"
sys.path.insert(0, str(OUROBOROS_DIR))

from run_ouroboros import check_doctor, run_audit



class TestOuroborosMetaPipeline(unittest.TestCase):
    def setUp(self):
        self.root_dir = Path(__file__).parent.parent
        self.ouroboros_dir = self.root_dir / "aidd-ouroboros"

    def test_meta_pipeline_files_exist(self):
        """Valida que todos os artefatos de governança do Ouroboros existem."""
        expected_files = [
            self.ouroboros_dir / "README.md",
            self.ouroboros_dir / "AGENTS.md",
            self.ouroboros_dir / "RULES.md",
            self.ouroboros_dir / "LICENSE",
            self.ouroboros_dir / "dependencies.json",
            self.ouroboros_dir / "OUROBOROS.json",
            self.ouroboros_dir / "run_ouroboros.py",
            self.ouroboros_dir / "schemas" / "HANDOFF.schema.json",
            self.ouroboros_dir / "references" / "00-manifesto-ouroboros.md",
        ]
        for f in expected_files:
            self.assertTrue(f.exists(), f"Arquivo ausente no Meta-Pipeline: {f}")

    def test_license_authorship(self):
        """Valida que o LICENSE formal atribui copyright a Heverton Eduardo Peres."""
        license_file = self.ouroboros_dir / "LICENSE"
        content = license_file.read_text(encoding="utf-8")
        self.assertIn("Heverton Eduardo Peres", content)
        self.assertIn("2026", content)

    def test_ouroboros_macro_nodes(self):
        """Valida a estrutura do Meta-DAG em OUROBOROS.json."""
        spec_file = self.ouroboros_dir / "OUROBOROS.json"
        with open(spec_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("meta_pipeline_id"), "aidd-ouroboros")
        nodes = data.get("macro_nodes", [])
        self.assertEqual(len(nodes), 4)
        node_ids = [n["id"] for n in nodes]
        self.assertIn("macro-01-ingestion-rea", node_ids)
        self.assertIn("macro-04-materialization-feedback", node_ids)


if __name__ == "__main__":
    unittest.main()
