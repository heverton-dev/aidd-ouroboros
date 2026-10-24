# RULES.md — Regras Inegociáveis e Gates do Orquestrador de Enxames

Este documento rege a execução de `aidd-skill-swarm`.  
Princípio Mestre: **"Toda regra sem um gate automatizado é apenas uma sugestão."**

---

## 1. Guardrails Negativos (Invariantes Mandatórias)

1. **R01 - NUNCA Duplicar Tarefas da Fábrica:**  
   O orquestrador NUNCA deve fabricar skills manualmente com código inline. Toda criação de nova skill DEVE ser delegada para a `aidd-skill-creator`.
2. **R02 - NUNCA Executar Pipeline Sem Validar Ciclos (DAG):**  
   O grafo de execução de skills deve ser um Grafo Acíclico Dirigido (DAG). Se houver dependência circular entre skills (A depende de B e B depende de A), o circuit breaker deve desarmar e travar o fluxo.
3. **R03 - NUNCA Ignorar o Inventário da Máquina:**  
   Antes de propor novas skills, o orquestrador DEVE varrer o computador do usuário (`--inventory`) e priorizar 100% o reuso de skills e MCPs que já existem instalados.
4. **R04 - NUNCA Romper o Contrato de Handoff:**  
   A comunicação entre as skills do enxame DEVE ocorrer exclusivamente por envelopes `HANDOFF.json`.
5. **R05 - Micro-Frontmatter Estrito:**  
   O frontmatter deste orquestrador deve respeitar o teto de 25 palavras.

---

## 2. Gates de Auditoria (`python skill_swarm.py --audit`)
- `G-MICRO-FRONTMATTER`: Valida $\le 25$ palavras na descrição do frontmatter.
- `G-DUAL-SPEC`: Valida `SKILL.md` e `AGENTS.md`.
- `G-GOVERNANCA`: Valida `RULES.md`, `LICENSE`, `pyproject.toml`, `dependencies.json` e `sync.ps1`.
- `G-CIRCUIT-BREAKER`: Valida implementação de `--doctor`, `--inventory`, `--plan` e `--audit`.
