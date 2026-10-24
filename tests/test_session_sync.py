"""
Teste automatizado para o Sincronizador de Sessao Universal (aidd-orchestrate-session-sync / faz-session).
"""

import json
from pathlib import Path
import sys
import tempfile
import unittest

SESSION_SYNC_SCRIPTS = Path(__file__).parent.parent / "aidd-skills" / "aidd-orchestrate-session-sync" / "scripts"
sys.path.insert(0, str(SESSION_SYNC_SCRIPTS))

from session_sync import (
    clean_user_prompt,
    parse_antigravity_transcript,
    parse_claude_transcript,
    sync_session_to_disk,
    run_audit,
)


class TestSessionSync(unittest.TestCase):
    def test_clean_user_prompt(self):
        """Valida que extrai o texto util de tags de prompt de sistema."""
        raw = "<USER_REQUEST>\nOla, este e meu prompt.\n</USER_REQUEST>\n<ADDITIONAL_METADATA>\ntime: 12:00\n</ADDITIONAL_METADATA>"
        cleaned = clean_user_prompt(raw)
        self.assertEqual(cleaned, "Ola, este e meu prompt.")

    def test_parse_antigravity_transcript_mock(self):
        """Valida parser do formato Antigravity / Gemini CLI."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_p = Path(tmp_dir)
            t_file = tmp_p / "brain" / "mock-uuid-1234" / ".system_generated" / "logs" / "transcript_full.jsonl"
            t_file.parent.mkdir(parents=True)

            lines = [
                json.dumps({
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "created_at": "2026-10-24T12:00:00Z",
                    "content": "<USER_REQUEST>\nPrimeiro prompt\n</USER_REQUEST>"
                }),
                json.dumps({
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-10-24T12:00:05Z",
                    "content": "Primeira resposta do modelo."
                }),
                json.dumps({
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "created_at": "2026-10-24T12:01:00Z",
                    "content": "<USER_REQUEST>\nSegundo prompt\n</USER_REQUEST>"
                }),
                json.dumps({
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-10-24T12:01:05Z",
                    "content": "Segunda resposta do modelo."
                })
            ]
            t_file.write_text("\n".join(lines), encoding="utf-8")

            s_id, dialogues, telemetry = parse_antigravity_transcript(t_file)
            self.assertEqual(s_id, "mock-uuid-1234")
            self.assertEqual(len(dialogues), 2)
            self.assertEqual(dialogues[0]["user_prompt"], "Primeiro prompt")
            self.assertEqual(dialogues[0]["model_response"], "Primeira resposta do modelo.")
            self.assertEqual(dialogues[1]["user_prompt"], "Segundo prompt")
            self.assertEqual(dialogues[1]["model_response"], "Segunda resposta do modelo.")
            self.assertIn("tokens_input", telemetry)
            self.assertIn("tokens_output", telemetry)

    def test_parse_claude_transcript_mock(self):
        """Valida parser do formato Claude Code."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            t_file = Path(tmp_dir) / "claude-session-5678.jsonl"
            lines = [
                json.dumps({"role": "user", "content": "Pergunta para Claude", "timestamp": "2026-10-24T13:00:00Z"}),
                json.dumps({"role": "assistant", "content": [{"type": "text", "text": "Resposta do Claude"}], "timestamp": "2026-10-24T13:00:02Z"})
            ]
            t_file.write_text("\n".join(lines), encoding="utf-8")

            s_id, dialogues, telemetry = parse_claude_transcript(t_file)
            self.assertEqual(s_id, "claude-session-5678")
            self.assertEqual(len(dialogues), 1)
            self.assertEqual(dialogues[0]["user_prompt"], "Pergunta para Claude")
            self.assertEqual(dialogues[0]["model_response"], "Resposta do Claude")
            self.assertIn("tokens_thinking", telemetry)

    def test_sync_session_to_disk_e2e(self):
        """Valida sincronizacao E2E com frontmatter estrito e persistencia."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_p = Path(tmp_dir)
            t_file = tmp_p / "transcript_full.jsonl"
            lines = [
                json.dumps({
                    "source": "USER_EXPLICIT",
                    "type": "USER_INPUT",
                    "created_at": "2026-10-24T14:00:00Z",
                    "content": "Criar pipeline Lego"
                }),
                json.dumps({
                    "source": "MODEL",
                    "type": "PLANNER_RESPONSE",
                    "created_at": "2026-10-24T14:00:03Z",
                    "input_tokens": 1500,
                    "output_tokens": 300,
                    "thinking": "Analisando a arquitetura de lego para compor o pipeline",
                    "content": "Pipeline Lego criado com sucesso."
                })
            ]
            t_file.write_text("\n".join(lines), encoding="utf-8")

            out_dir = tmp_p / "output_secoes"
            res = sync_session_to_disk(
                transcript_path=str(t_file),
                session_id="test-e2e-session",
                output_dir=str(out_dir),
                export_format="all"
            )

            self.assertEqual(res["total_turns"], 1)
            
            # Encontrar arquivo com prefixo de data DDMMAAAA_test-e2e-session.json e .md
            files_found = list(out_dir.rglob("*_test-e2e-session.json"))
            self.assertTrue(len(files_found) == 1)
            target_json = files_found[0]

            files_found_md = list(out_dir.rglob("*_test-e2e-session.md"))
            self.assertTrue(len(files_found_md) == 1)
            target_md = files_found_md[0]

            # Validar que o Markdown foi gerado com cabecalho limpo, comandos de restauracao e prompt copiavel
            md_text = target_md.read_text(encoding="utf-8")
            self.assertTrue(md_text.startswith("# 📋 Sessão `test-e2e-session`"))
            self.assertIn("### 🔄 Comandos de Restauração da Sessão", md_text)
            self.assertIn("agy --conversation test-e2e-session", md_text)
            self.assertIn("claude --resume test-e2e-session", md_text)
            self.assertIn("opencode --session test-e2e-session", md_text)
            self.assertIn("mimo --session test-e2e-session", md_text)
            self.assertIn("omp --resume test-e2e-session", md_text)
            self.assertIn("hermes --resume test-e2e-session", md_text)
            self.assertIn("### 👤 User Prompt", md_text)
            self.assertIn("```", md_text)
            self.assertIn("Criar pipeline Lego", md_text)
            self.assertIn("### 🤖 Model Response", md_text)
            self.assertIn("Pipeline Lego criado com sucesso.", md_text)

            # Validar frontmatter estrito
            data = json.loads(target_json.read_text(encoding="utf-8"))
            self.assertEqual(data["id_sessao"], "test-e2e-session")
            self.assertIn("frontmatter", data)
            fm = data["frontmatter"]
            self.assertEqual(fm["id_sessao"], "test-e2e-session")
            self.assertIn("harness_utilizado", fm)
            self.assertIn("projeto", fm)
            self.assertIn("branch", fm)
            self.assertEqual(fm["tokens_input"], 1500)
            self.assertEqual(fm["tokens_input_formatado"], "1.500")
            self.assertEqual(fm["tokens_output"], 300)
            self.assertEqual(fm["tokens_output_formatado"], "300")
            self.assertIn("resumo_tokens", fm)
            self.assertTrue(fm["tokens_thinking"] > 0)
            self.assertEqual(len(data["dialogos"]), 1)

    def test_audit_session_sync_gates(self):
        """Valida que a skill passa na auditoria dos 4 Gates do Ouroboros."""
        skill_dir = SESSION_SYNC_SCRIPTS.parent
        self.assertTrue(run_audit(str(skill_dir)))


if __name__ == "__main__":
    unittest.main()
