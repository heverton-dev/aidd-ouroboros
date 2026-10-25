# Contexto de Entrada: _e2e-smoke

Este diretório armazena os dados sintéticos de teste e fixtures mínimas para a verificação de fumaça (smoke test) E2E do motor Ouroboros.

## Contrato de Dados
- **Formato:** JSON sintético, fixtures mínimas de teste.
- **Ciclo de Vida:** Consumido pelo pipeline de smoke test em validações de CI/CD e auditoria local.
- **Persistência:** Ficheiros gerados durante a execução do smoke test são efêmeros.
