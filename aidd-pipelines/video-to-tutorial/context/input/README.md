# Contexto de Entrada: video-to-tutorial

Este diretório armazena os arquivos de vídeo de origem, links ou especificações de entrada para extração e geração de tutoriais.

## Contrato de Dados
- **Formato:** URLs do YouTube, referências de arquivos MP4/MKV ou transcrições brutas.
- **Ciclo de Vida:** Processado pelo nó de engenharia reversa (`aidd-rea-video-youtube`) para decomposição de frames e áudio.
- **Persistência:** Arquivos de vídeo e dados transitórios são ignorados pelo Git.
