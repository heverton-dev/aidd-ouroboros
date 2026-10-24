# RULES.md — Regras Inegociáveis e Gates (aidd-remotion-motion)

Princípio Mestre: "Toda regra sem um gate automatizado é apenas uma sugestão."

1. **R01:** NUNCA emitir saídas stub sem implementação funcional.
2. **R02:** NUNCA violar o contrato de portabilidade.
3. **R03:** NUNCA estourar o orçamento de contexto.

## Gates de Auditoria
- `python scripts/remotion_motion.py --audit` valida a conformidade dos entregáveis.
