# RULES.md - Gates e Circuit Breakers do Pipeline

Regras de conformidade e criterios de parada obrigatorios.

## Gate 1: Integridade de Entrada
- O primeiro no do DAG valida a existencia de `context/input/pipeline_input.json`.

## Gate 2: Conformidade de Handoff
- Todo no intermediario DEVE emitir envelope JSON valido.

## Gate 3: Envelope de Saida Lego
- Ao concluir todos os nos com sucesso, o runner DEVE emitir `context/output/pipeline_output.json`.
