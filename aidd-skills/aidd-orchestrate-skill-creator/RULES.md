# RULES.md — Regras Inegociáveis e Gates da Meta-Skill

Este documento rege a execução de `aidd-skill-creator`.  
Princípio Mestre: **"Toda regra sem um gate automatizado é apenas uma sugestão."**

---

## 1. Guardrails Negativos (Invariantes Mandatórias)

1. **R01 - NUNCA Estourar o Orçamento de Tokens no Frontmatter:**  
   A descrição da nova skill no `SKILL.md` DEVE conter no máximo **25 palavras** e focar exclusivamente em gatilhos imperativos. Qualquer skill gerada com mais de 25 palavras no frontmatter será reprovada no `GATE_TOKEN_BUDGET`.
2. **R02 - NUNCA Gerar Skills Mono-Arquivo (Legado):**  
   Toda nova skill deve conter o scaffolding completo de 8 diretórios (`scripts/`, `references/`, `templates/`, etc.) e suporte a `sync.ps1` e `sync.sh`.
3. **R03 - NUNCA Gerar Código Sem Validação (--audit):**  
   Toda skill gerada deve nascer com seu próprio script CLI contendo os subcomandos `--doctor`, `--setup` e `--audit` com Circuit Breakers.
4. **R04 - NUNCA Avançar sem Aprovação do SPEC:**  
   Em qualquer modo de ingestão (`socratic`, `doc`, `image`), o interrogatório deve produzir `SPEC_SKILL.json` e exigir aprovação humana explícita antes da geração física dos arquivos.
5. **R05 - NUNCA Omitir Licença e Autoria:**  
   Toda skill deve conter o arquivo `LICENSE` no padrão MIT com o autor informado.

---

## 2. Gates Binários de Validação da Skill Gerada

O comando `python skill_creator.py --audit <PASTA>` valida:

* **GATE 1 (`G-MICRO-FRONTMATTER`):** Audita o frontmatter YAML do `SKILL.md`. Verifica se a `description` tem $\le 25$ palavras para proteger o system prompt do usuário.
* **GATE 2 (`G-DUAL-SPEC`):** Verifica a presença conjunta de `SKILL.md` e `AGENTS.md`.
* **GATE 3 (`G-GOVERNANCA`):** Verifica a presença de `RULES.md`, `LICENSE`, `pyproject.toml`, `requirements.txt` e scripts de sync (`sync.ps1` / `sync.sh`).
* **GATE 4 (`G-CIRCUIT-BREAKER`):** Verifica se o script principal da skill possui implementação de `--doctor` e `--audit`.
