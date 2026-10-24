"""
Teste automatizado para o Criador e Garimpador de Pipelines (aidd-orchestrate-pipeline-creator).
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

# Adicionar aidd-orchestrate-pipeline-creator ao path
CREATOR_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-orchestrate-pipeline-creator" / "scripts"
sys.path.insert(0, str(CREATOR_SCRIPTS))

import pipeline_creator
from pipeline_creator import (
    scaffold_autonomous_pipeline,
    scout_local_pipelines,
    scout_github_for_pipeline,
    load_pipeline_scout_cache,
    save_pipeline_scout_cache,
)


class TestPipelineCreator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_cache = Path(self.temp_dir.name) / "github_pipeline_scout_cache.json"
        self.original_get_cache = pipeline_creator.get_pipeline_scout_cache_path
        pipeline_creator.get_pipeline_scout_cache_path = lambda: self.temp_cache

    def tearDown(self):
        pipeline_creator.get_pipeline_scout_cache_path = self.original_get_cache
        self.temp_dir.cleanup()

    def test_scaffold_autonomous_pipeline_lego(self):
        """Valida que scaffold_autonomous_pipeline cria a estrutura completa de Lego composível."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            pipeline_dir = scaffold_autonomous_pipeline("demo-pipeline", base_dir=tmp_path)

            self.assertTrue(pipeline_dir.exists())
            self.assertTrue((pipeline_dir / "README.md").exists())
            self.assertTrue((pipeline_dir / "AGENTS.md").exists())
            self.assertTrue((pipeline_dir / "RULES.md").exists())
            self.assertTrue((pipeline_dir / "LICENSE").exists())
            self.assertTrue((pipeline_dir / "dependencies.json").exists())
            self.assertTrue((pipeline_dir / "PIPELINE.json").exists())
            self.assertTrue((pipeline_dir / "run_pipeline.py").exists())
            self.assertTrue((pipeline_dir / "state.json").exists())
            self.assertTrue((pipeline_dir / "references").is_dir())
            self.assertTrue((pipeline_dir / "templates").is_dir())
            self.assertTrue((pipeline_dir / "context" / "input").is_dir())
            self.assertTrue((pipeline_dir / "context" / "handoffs").is_dir())
            self.assertTrue((pipeline_dir / "context" / "output").is_dir())
            self.assertTrue((pipeline_dir / "skills").is_dir())

            # Validar autoria Heverton Eduardo Peres
            license_text = (pipeline_dir / "LICENSE").read_text(encoding="utf-8")
            self.assertIn("Heverton Eduardo Peres", license_text)

            # Validar interoperabilidade Lego no PIPELINE.json
            with open(pipeline_dir / "PIPELINE.json", "r", encoding="utf-8") as f:
                spec = json.load(f)
            self.assertEqual(spec["pipeline_id"], "demo-pipeline")
            self.assertEqual(spec.get("pipeline_type"), "autonomous_lego_pipeline")
            self.assertEqual(spec.get("input_contract"), "context/input/pipeline_input.json")
            self.assertEqual(spec.get("output_contract"), "context/output/pipeline_output.json")
            self.assertGreaterEqual(len(spec["nodes"]), 1)

    def test_scout_local_pipelines(self):
        """Valida que scout_local_pipelines localiza pipelines canônicos e workflows."""
        root = Path(__file__).parent.parent
        pipelines = scout_local_pipelines(root)
        self.assertIsInstance(pipelines, list)
        self.assertGreaterEqual(len(pipelines), 1)
        # Deve encontrar ao menos um pipeline em aidd-pipelines/
        names = [p["name"] for p in pipelines]
        self.assertTrue(any("canal-dark" in n.lower() or "video-to-tutorial" in n.lower() for n in names))

    def test_pipeline_scout_cache_anti_ban(self):
        """Valida que o cache de pipeline scout previne chamadas externas (Zero-Tokens / Anti-Ban)."""
        cache_data = {
            "addyosmani workflow": {
                "timestamp": 9999999999.0,
                "results": [
                    {
                        "name": "addyosmani-agent-workflow",
                        "owner": {"login": "addyosmani"},
                        "description": "Enterprise agent pipeline",
                        "stargazersCount": 500,
                        "license": {"key": "mit"},
                        "url": "https://github.com/addyosmani/agent-workflow"
                    }
                ]
            }
        }
        save_pipeline_scout_cache(cache_data)

        # Buscar com a query em cache
        res = scout_github_for_pipeline("addyosmani workflow", min_stars=50)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["name"], "addyosmani-agent-workflow")


if __name__ == "__main__":
    unittest.main()
