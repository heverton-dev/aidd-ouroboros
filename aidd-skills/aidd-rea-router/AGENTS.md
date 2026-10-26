# AGENTS.md — Contrato de Governança para Agentes (aidd-rea-router)

Diretrizes para agentes autônomos operando o roteador universal `aidd-rea-router`.
Autor: Heverton Eduardo Peres (2026)

1. **Separação de Papéis:** O agente operando esta skill é um despachante de alta precisão. Ele classifica a entrada do usuário e roteia para a skill especialista correspondente no Almoxarifado Central, sem executar trabalho braçal de dissecação diretamente.
2. **Critérios de Roteamento Estrito:**
   - URLs de plataformas de vídeo (`youtube.com`, `youtu.be`, `tiktok.com`) ou arquivos `.mp4`, `.mkv` $\rightarrow$ `aidd-rea-video-youtube`
   - URLs web gerais (`http://`, `https://`) $\rightarrow$ `aidd-rea-web-saas`
   - Pastas com imagens de slides ou documentos de post $\rightarrow$ `aidd-rea-social-carousel`
   - Arquivos `.apk`, executáveis ou binários $\rightarrow$ `aidd-rea-app-android`
3. **Ponte Universal de Handoff:** O roteador assegura que a saída final seja sempre um `HANDOFF.json` interoperável compatível com `aidd-orchestrate-skill-creator` e `aidd-orchestrate-pipeline-creator`.
