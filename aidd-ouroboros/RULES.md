# RULES.md — Gates e Circuit Breakers Globais (aidd-ouroboros)

Invariantes e criterios de parada obrigatorios para o ecossistema AIDD.

## Gate 1: Micro-Frontmatter Estrito
- O campo description no frontmatter YAML de qualquer SKILL.md gerada DEVE conter no maximo 25 palavras.
- Violacoes desarmam imediatamente o auditor e impedem a liberacao da skill.

## Gate 2: Padrao Dual-Spec Obrigatorio
- Toda unidade de software do ecossistema DEVE conter tanto SKILL.md (ou README.md) quanto AGENTS.md.

## Gate 3: Governanca de Autoria e Licenca
- Toda skill, pipeline ou modulo DEVE conter arquivo LICENSE com copyright atribuido a Heverton Eduardo Peres (2026).

## Gate 4: Restricao de Simbolos e Emojis
- Codigo-fonte, documentacao e logs gerados DEVEM manter estilo tecnico formal, sem o uso de caracteres pictograficos ou emojis.
