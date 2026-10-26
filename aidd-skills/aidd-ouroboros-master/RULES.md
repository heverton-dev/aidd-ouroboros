# RULES.md — Regras Inegociáveis (aidd-ouroboros-master)

Princípio: "Toda regra sem gate automatizado é apenas uma sugestão."

1. **R01:** Spec sem `approved: true` → exit 2; sem orquestração.
2. **R02:** Placeholders (`PREENCHER`, `placeholder-pipeline`) → exit 3 + entrevista.
3. **R03:** Zero stubs no Python desta skill (gate AST).
4. **R04:** Micro-frontmatter ≤ 25 palavras.
5. **R05:** Handoffs assinados com HMAC; chave fail-closed.
6. **R06:** F2 só encadeia CLIs canônicos; nunca LLM improvisando scaffold.

## Gates
- `python scripts/ouroboros_master.py --audit`
- `python scripts/ouroboros_master.py --doctor`
