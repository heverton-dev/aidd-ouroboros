# Fundamentos da Engenharia Reversa Web (REA Web Protocol)

Documento conceitual que estabelece a metodologia de dissecação de aplicações web e SaaS no padrão AIDD.

## 1. Princípios de Dissecação
1. **Fidelidade Computada:** Preferir propriedades computadas do CSS a estilos inline parciais.
2. **Tokens como Fonte Única da Verdade (SSOT):** Extrair paleta de cores normalizada em hex/hsl e escalas de fonte em rem/px.
3. **Mapeamento de Ações:** Identificar todos os elementos interativos (`button`, `a`, `form`, `input`).
4. **Isolamento de Estado:** Todo artefato extraído deve residir em sua pasta de evidências sem interferir em outros módulos.
