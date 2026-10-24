# AGENTS.md — Contrato Operacional para Agentes Autônomos

Este arquivo define as diretrizes de execução, limites e invariantes para agentes de IA (Claude Code, Antigravity, Cursor, Hermes, OpenCode, Codex) ao executarem tarefas dentro da skill `aidd-video-reengineer`.

---

## 1. Princípios de Invariância (Leis Inegociáveis)

1. **Protocolo de Evidência REA (Zero Alucinação):**  
   O agente NUNCA deve inventar comandos, ferramentas ou parâmetros que o criador não demonstrou.
   * Toda afirmação em `metodologia.md` deve conter obrigatoriamente um rótulo:
     - `[OBSERVADO NO FRAME]`
     - `[DITO NO ÁUDIO]`
     - `[DERIVADO]`
     - `[DESCONHECIDO REA]`
2. **Prioridade ao Determinismo:**  
   Sempre use as ferramentas locais do script `video_reengineer.py` (download, faster-whisper, ffmpeg e tesseract local). Nunca gaste tokens de modelo multimodal para tarefas que o binário local executa com custo zero.
3. **Padrão de Nomenclatura Canônica:**  
   As pastas de vídeos extraídos NUNCA devem conter apenas o ID opaco. O padrão obrigatório é:
   `research/videos/<VIDEO_ID>--<autor>-<slug-curto>`
4. **Scaffolding em 3 Camadas:**  
   Não coloque arquivos soltos na raiz da pasta do vídeo. Respeite as subpastas `raw/`, `transcricao/` e `visual/`. A raiz é reservada exclusivamente para `manifest.json`, `metodologia.md` e `gap_analysis.md`.
5. **Filosofia `aidd-lauren` (*pstack*):**  
   Ao gerar `gap_analysis.md`, aplique `unslop` para podar etapas manuais do autor (ex: edição em DaVinci) e `principle-prove-it-works` nos nano-tickets.
6. **Lentes de Dissecação (--analise):**  
   - Use `--analise conteudo` para extrair ferramentas, APIs, código e comandos técnicos (`conteudo_tecnico.md`).
   - Use `--analise estrutura` para dissecar a Thumbnail OCR, o Hook inicial (0-15s), ritmo de corte, descrição do YouTube e CTA (`estrutura_narrativa.md`).
   - Use `--analise full` (padrão) para gerar o pacote completo.


---

## 2. Roteamento de Comandos Rápidos

* **Diagnóstico de Ambiente:**
  ```bash
  python aidd-video-reengineer/scripts/video_reengineer.py --doctor
  ```
* **Dissecação Primária com Nomenclatura Automática:**
  ```bash
  python aidd-video-reengineer/scripts/video_reengineer.py "<URL_YOUTUBE>" --intervalo-frames 10
  ```
* **Sincronização entre Ambientes:**
  ```powershell
  powershell -File aidd-video-reengineer/sync.ps1
  ```
