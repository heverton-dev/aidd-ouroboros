# 00 — Fundamentos do meta-fluxo

## Por que existe
O usuário pede um pipeline em NL. Sem spec fechada, qualquer agente inventa skills e DAGs (viola determinismo).

## Contrato
- **F1:** entrevista → `SPEC_PIPELINE.json` (schema em `schemas/SPEC_PIPELINE.schema.json`)
- **F2:** `--orchestrate` valida → REA (opcional) → skills → scaffold → deps → audit

## Exit codes
| Code | Significado | Ação do agente |
|------|-------------|----------------|
| 0 | Sucesso | Entregar caminho do pipeline |
| 1 | Erro técnico | Inspecionar logs / state |
| 2 | Não aprovado | Voltar à F1 |
| 3 | Dúvida | Mini-entrevista + `--resume` |

## Estado
`ouroboros_master_state.json` e `pending_question.json` no cwd de execução.
