"""
Teste automatizado para o GitHub Scout & Canonize do aidd-orchestrate-skill-creator.
"""

from pathlib import Path
import sys
import tempfile
import unittest

# Adicionar aidd-orchestrate-skill-creator ao sys.path
CREATOR_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-orchestrate-skill-creator" / "scripts"
sys.path.insert(0, str(CREATOR_SCRIPTS))

from skill_creator import (
    DEFAULT_AUTHOR,
    count_words,
    extract_frontmatter_description,
    scout_and_canonize_skill,
)


class TestSkillCreatorGithubScout(unittest.TestCase):
    def test_scout_and_canonize_generates_canonical_skill(self):
        """Valida que uma busca ou fallback gera skill com prefixo aidd-, Micro-Frontmatter e gates."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            skill_dir = scout_and_canonize_skill(
                query="whisper subtitles",
                author=DEFAULT_AUTHOR,
                output_base=tmp_path,
                min_stars=20,
            )

            self.assertTrue(skill_dir.exists())
            self.assertTrue(skill_dir.name.startswith("aidd-"))
            self.assertTrue((skill_dir / "SKILL.md").exists())
            self.assertTrue((skill_dir / "AGENTS.md").exists())
            self.assertTrue((skill_dir / "RULES.md").exists())
            self.assertTrue((skill_dir / "LICENSE").exists())
            self.assertTrue((skill_dir / "dependencies.json").exists())
            self.assertTrue((skill_dir / "HANDOFF.json").exists())

            # Validar Micro-Frontmatter <= 25 palavras
            desc = extract_frontmatter_description(skill_dir / "SKILL.md")
            words = count_words(desc)
            self.assertLessEqual(words, 25, f"Micro-Frontmatter excedeu 25 palavras: {words}")

            # Validar autoria na licença
            license_text = (skill_dir / "LICENSE").read_text(encoding="utf-8")
            self.assertIn("Heverton Eduardo Peres", license_text)

            # Validar proveniência registrada
            provenance_file = skill_dir / "references" / "00-upstream-provenance.md"
            self.assertTrue(provenance_file.exists())


if __name__ == "__main__":
    unittest.main()
