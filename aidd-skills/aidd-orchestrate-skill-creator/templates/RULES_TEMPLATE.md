# RULES.md — Regras Inegociáveis e Gates ({{SKILL_NAME}})

Princípio Mestre: **"Toda regra sem um gate automatizado é apenas uma sugestão."**

---

## 1. Guardrails Negativos
- **R01:** NUNCA violar o contrato de dados sem validação.
- **R02:** NUNCA emitir tarefas ou saídas stub.
- **R03:** NUNCA estourar limites de contexto.

---

## 2. Gates de Auditoria (`python scripts/{{SCRIPT_NAME}}.py --audit`)
- `GATE 1`: Conformidade de entradas e saídas.
- `GATE 2`: Integridade dos testes de validação.
