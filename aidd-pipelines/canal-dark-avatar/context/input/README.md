# Contexto de Entrada: canal-dark-avatar

Este diretório armazena os payloads de entrada, briefings brutos e parâmetros iniciais para a execução do pipeline `canal-dark-avatar`.

## Contrato de Dados
- **Formato:** JSON / Markdown / Audio / Imagens de referência.
- **Ciclo de Vida:** Artefatos colocados aqui são consumidos como leitura pelos nós iniciais do DAG (`aidd-craft-story-ptbr`, `aidd-materialize-video-synth`).
- **Persistência:** Arquivos temporários e dados dinâmicos são ignorados pelo Git via `.gitignore`.
