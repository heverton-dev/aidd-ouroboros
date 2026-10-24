# 00 — Anatomia Canônica de uma Skill Enterprise

Uma skill de padrão de fronteira adota 8 componentes obrigatórios:

1. **`SKILL.md`:** Roteador principal com Micro-Frontmatter ($\le 25$ palavras), tabela de portabilidade, gatilhos de ativação, fluxo em fases e gates binários.
2. **`AGENTS.md` (Dual-Spec):** Contrato em Markdown simples para harnesses que leem regras na raiz.
3. **`README.md`:** Manual de onboarding e instrução para humanos e CI/CD.
4. **`RULES.md`:** Guardrails negativos ("o que NUNCA fazer") e regras de desarme (circuit breakers).
5. **`LICENSE`:** Licença MIT no nome do autor para garantia jurídica.
6. **`pyproject.toml` + `requirements.txt`:** Gerenciamento declarativo via `uv` e `pip`.
7. **`scripts/`:** Ferramentas executáveis locais com subcomandos obrigatórios:
   - `--doctor`: Diagnóstico de ambiente.
   - `--setup`: Instalação one-liner e propagação.
   - `--audit`: Auditor de conformidade dos gates.
8. **`sync.ps1` e `sync.sh`:** Propagação para as 13 pastas de skills do sistema.
