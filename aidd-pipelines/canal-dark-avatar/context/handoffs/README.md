# Contexto de Handoffs: canal-dark-avatar

Este diretório gerencia os manifests de transição e passagens de bastão criptográficas (HMAC-SHA256) entre as etapas do pipeline `canal-dark-avatar`.

## Contrato de Dados
- **Formato:** Manifests `manifest.json` com `path`, `sha256` e assinatura gerada por `motores/governanca/handoff_crypto.py`.
- **Integridade:** Ponteiros locais validados determinísticamente antes da ingestão pelo nó subsequente.
- **Persistência:** Handoffs de execução em tempo real são efêmeros e ignorados pelo controle de versão.
