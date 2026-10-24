# AGENTS.md — Contrato de Governança para Agentes (aidd-remotion-motion)

Diretrizes para agentes de IA operando a skill `aidd-remotion-motion`.
Autor: Heverton Eduardo Peres

1. **Eficiência de Contexto:** Não leia todas as referências antecipadamente. Pratique Lazy Loading lendo apenas o arquivo de `references/` da etapa ativa.
2. **Determinismo:** Sempre execute os scripts de `scripts/` antes de tentar deduções de texto.
3. **Gates:** Valide a entrega rodando `python scripts/remotion_motion.py --audit`.
