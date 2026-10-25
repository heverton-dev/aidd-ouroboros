# Pipeline DAG Specification & Architectural Constraints

## 1. Topologia Acíclica
Pipelines no ecossistema Ouroboros são estruturados como Grafos Acíclicos Direcionados (DAGs).
- Cada nó representa uma etapa (`step`) executada por uma skill canônica.
- Transições de estado entre etapas requerem handoffs criptográficos imutáveis via HMAC-SHA256.

## 2. Contrato de Entrada e Saída
1. **Entrada (`context/input`):** Dados brutos ingeridos com checagem de hash.
2. **Handoffs intermediários (`context/handoffs`):** Manifestos `manifest.json` com ponteiros locais (`path`, `sha256`).
3. **Saída (`context/output`):** Artefato final consolidado com assinatura de integridade.
