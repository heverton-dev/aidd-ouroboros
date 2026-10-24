# AGENTS.md — Contrato de Governança para Agentes ({{SKILL_NAME}})

Diretrizes para agentes de IA operando a skill `{{SKILL_NAME}}`.
Padrão: AIDD Universal Architecture / Zero Stubs / Token Economy (< 350t).

---

## 1. Princípios de Execução Invioláveis

1. **Eficiência de Contexto (Lazy Loading):** Não carregue referências antecipadamente. Leia apenas o arquivo necessário em `references/` para a fase atual.
2. **Economia Extrema de Tokens (Pointer Architecture):** Nunca despeje conteúdos massivos no prompt. Troque apenas caminhos de arquivos e hashes SHA-256 via envelopes de handoff.
3. **Determinismo:** Sempre execute os scripts locais em `scripts/` antes de tentar deduções de texto via LLM.
4. **Zero Stubs / Zero Mocks:** Código gerado deve ser completo e tipado. Proibido o uso de `pass`, `TODO` ou `NotImplementedError` em funções de negócio.
5. **Quality Gates:** Toda entrega deve passar no gate AST (`python -m motores.governanca.gate_ast`).
