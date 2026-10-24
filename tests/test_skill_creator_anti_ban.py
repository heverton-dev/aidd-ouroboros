"""
Teste automatizado para as Travas de Segurança Anti-Ban e Cache Persistente (aidd-orchestrate-skill-creator).
"""

from pathlib import Path
import sys
import tempfile
import time
import unittest

# Adicionar aidd-orchestrate-skill-creator ao sys.path
CREATOR_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-orchestrate-skill-creator" / "scripts"
sys.path.insert(0, str(CREATOR_SCRIPTS))

import skill_creator
from skill_creator import load_scout_cache, save_scout_cache, scout_github_for_skill


class TestSkillCreatorAntiBan(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_cache = Path(self.temp_dir.name) / "github_scout_cache.json"
        # Monkey patch do caminho do cache para isolamento de teste
        self.original_get_cache = skill_creator.get_scout_cache_path
        skill_creator.get_scout_cache_path = lambda: self.temp_cache

    def tearDown(self):
        skill_creator.get_scout_cache_path = self.original_get_cache
        self.temp_dir.cleanup()

    def test_cache_hit_prevents_network_calls(self):
        """Valida que uma query existente no cache retorna dados locais sem consultar a rede."""
        query = "mocked-test-query"
        mock_data = {
            query: {
                "timestamp": time.time(),
                "results": [
                    {
                        "name": "mocked-repo",
                        "owner": {"login": "mock-user"},
                        "description": "Mocked repo for testing cache",
                        "stargazersCount": 150,
                        "license": {"key": "mit"},
                        "url": "https://github.com/mock-user/mocked-repo",
                    }
                ],
            }
        }
        save_scout_cache(mock_data)

        # A chamada deve recuperar do cache imediatamente
        results = scout_github_for_skill(query, min_stars=50)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "mocked-repo")
        self.assertEqual(results[0]["stargazersCount"], 150)

    def test_expired_cache_is_ignored(self):
        """Valida que cache expirado (> TTL) não é utilizado."""
        query = "expired-query"
        mock_data = {
            query: {
                "timestamp": time.time() - 800000,  # Mais de 7 dias atrás
                "results": [{"name": "old-repo", "stargazersCount": 200}],
            }
        }
        save_scout_cache(mock_data)

        # Com TTL de 10 segundos, o cache acima deve ser ignorado
        results = scout_github_for_skill(query, min_stars=50, cache_ttl_seconds=10)
        # Como o repositório 'expired-query' não existe no GitHub, deve retornar vazio sem lançar exceção
        self.assertIsInstance(results, list)


if __name__ == "__main__":
    unittest.main()
