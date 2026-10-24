"""
Teste automatizado para o Ciclo de Vida e Evolução de Skills e Pipelines (AIDD Evolution Engine).
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

# Caminhos das skills de criação
ROOT_DIR = Path(__file__).parent.parent
SKILL_CREATOR_SCRIPTS = ROOT_DIR / "aidd-skills" / "aidd-orchestrate-skill-creator" / "scripts"
PIPELINE_CREATOR_SCRIPTS = ROOT_DIR / "aidd-skills" / "aidd-orchestrate-pipeline-creator" / "scripts"

sys.path.insert(0, str(SKILL_CREATOR_SCRIPTS))
sys.path.insert(0, str(PIPELINE_CREATOR_SCRIPTS))

from skill_creator import create_canonical_skill, evolve_skill
from pipeline_creator import scaffold_autonomous_pipeline, evolve_pipeline


class TestEvolutionLifecycle(unittest.TestCase):
    def test_evolve_skill_lifecycle(self):
        """Valida que evolve_skill incrementa versão, registra log, atualiza contratos e passa nos gates."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # 1. Criar skill inicial
            skill_dir = create_canonical_skill(
                output_base=tmp_path,
                name="aidd-test-evolving",
                author="Heverton Eduardo Peres",
                micro_desc="Skill de teste para validacao de ciclo evolutivo continuo.",
                mission="executar testes automatizados de evolucao",
                templates_dir=None
            )

            # Validar versão inicial
            dep_data = json.loads((skill_dir / "dependencies.json").read_text(encoding="utf-8"))
            self.assertEqual(dep_data["version"], "1.0.0")

            # 2. Executar evolução
            evolved_dir = evolve_skill(
                skill_target=str(skill_dir),
                spec="Adicionar suporte a sintese neural assincrona e batching",
                author="Heverton Eduardo Peres"
            )

            # Validar que a versão foi bumpada para 1.1.0
            dep_data_evo = json.loads((evolved_dir / "dependencies.json").read_text(encoding="utf-8"))
            self.assertEqual(dep_data_evo["version"], "1.1.0")

            pyproject_text = (evolved_dir / "pyproject.toml").read_text(encoding="utf-8")
            self.assertIn('version = "1.1.0"', pyproject_text)

            # Validar log de evolução
            evo_log = (evolved_dir / "references" / "EVOLUTION_LOG.md").read_text(encoding="utf-8")
            self.assertIn("[v1.1.0]", evo_log)
            self.assertIn("Adicionar suporte a sintese neural", evo_log)
            self.assertIn("Heverton Eduardo Peres", evo_log)

            # Validar diretriz em AGENTS.md
            agents_text = (evolved_dir / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Capacidade v1.1.0", agents_text)

    def test_evolve_pipeline_add_and_remove_step(self):
        """Valida que evolve_pipeline insere e remove nós do DAG mantendo contratos Lego."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # 1. Criar pipeline inicial (3 nós padrão)
            p_dir = scaffold_autonomous_pipeline("pipeline-evolutivo", base_dir=tmp_path)
            with open(p_dir / "PIPELINE.json", "r", encoding="utf-8") as f:
                spec_initial = json.load(f)
            self.assertEqual(len(spec_initial["nodes"]), 3)

            # 2. Adicionar uma nova etapa após o node-02-creator
            evolve_pipeline(
                pipeline_target=str(p_dir),
                add_step="aidd-materialize-tutorial-stitch",
                after_node="node-02-creator",
                spec="Compor tutorial de video animado final"
            )

            with open(p_dir / "PIPELINE.json", "r", encoding="utf-8") as f:
                spec_after_add = json.load(f)
            
            # Deve conter 4 nós
            self.assertEqual(len(spec_after_add["nodes"]), 4)
            node_ids = [n["id"] for n in spec_after_add["nodes"]]
            self.assertIn("node-04-materialize-tutorial-stitch", node_ids)

            # O último nó deve apontar para pipeline_output.json
            self.assertEqual(spec_after_add["nodes"][-1]["output_handoff"], "context/output/pipeline_output.json")

            # Validar EVOLUTION_LOG.md do pipeline
            evo_log = (p_dir / "references" / "EVOLUTION_LOG.md").read_text(encoding="utf-8")
            self.assertIn("Adicionar aidd-materialize-tutorial-stitch", evo_log)

            # 3. Remover um nó do DAG
            evolve_pipeline(
                pipeline_target=str(p_dir),
                remove_step_id="node-01-ingest",
                spec="Remover ingestao redundante"
            )

            with open(p_dir / "PIPELINE.json", "r", encoding="utf-8") as f:
                spec_after_remove = json.load(f)

            self.assertEqual(len(spec_after_remove["nodes"]), 3)
            node_ids_final = [n["id"] for n in spec_after_remove["nodes"]]
            self.assertNotIn("node-01-ingest", node_ids_final)


if __name__ == "__main__":
    unittest.main()
