# Contexto de Handoffs: video-to-tutorial

Este diretório armazena os estados intermediários e passagens de bastão criptográficas (HMAC-SHA256) entre a dissecação do vídeo e a redação do tutorial.

## Contrato de Dados
- **Formato:** Manifests `manifest.json` com apontamento para snapshots de frames, transcrições pontuais e análise de tópicos.
- **Integridade:** Validação estrita por hashes locais antes da passagem para `aidd-craft-story-ptbr`.
- **Persistência:** Conteúdo gerado em runtime é efêmero e não versionado.
