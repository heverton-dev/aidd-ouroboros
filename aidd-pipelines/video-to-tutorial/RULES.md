# Regras de Execução: Pipeline video-to-tutorial

## 1. Diretrizes de Governança
- **Extração Factual:** Transcrição e extração de quadros devem preservar rigorosamente a ordem temporal do vídeo de entrada.
- **Handoff Criptográfico:** Todo estágio deve ler e emitir manifestos de integridade HMAC-SHA256.
- **Validação de Sintaxe:** Todo código gerado a partir do vídeo deve passar por validação de integridade e formatação.
- **Sem Intervenção Manual:** Execução em lote via DAG determinístico sem prompts iterativos redundantes.
