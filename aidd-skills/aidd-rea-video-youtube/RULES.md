# RULES.md — Regras Inegociáveis, Gates e Circuit Breakers

Este documento define as regras mandatórias da skill `aidd-video-reengineer`.  
No ecossistema AIDD: **"Toda regra sem um gate automatizado é apenas uma sugestão."**

---

## 1. Guardrails Negativos (O que NUNCA fazer)

1. **R01 - NUNCA Alucinar Detalhes Omitidos:**  
   Se o autor do vídeo não mostrou o código de uma biblioteca ou como sincronizou o áudio, é TERMINANTEMENTE PROIBIDO inventar uma solução fictícia e tratá-la como se o autor tivesse ensinado aquilo. A omissão DEVE ser marcada obrigatoriamente como `[DESCONHECIDO REA]`.
2. **R02 - NUNCA Usar Visão de LLM para Tarefas Locais:**  
   É PROIBIDO consumir tokens multimodais para ler imagens em lote se o binário local do Tesseract OCR puder extrair o texto em 0 tokens.
3. **R03 - NUNCA Criar Nano-Tickets Stub:**  
   É PROIBIDO criar tickets cujo comando de validação seja `echo ok`, `exit 0`, `true` ou qualquer comando que não possa falhar antes da implementação.
4. **R04 - NUNCA Poluir a Raiz do Vídeo:**  
   É PROIBIDO salvar arquivos de áudio, vídeo ou transcrição soltos na raiz da pasta do vídeo. O scaffolding deve respeitar estritamente `raw/`, `transcricao/` e `visual/`.
5. **R05 - NUNCA Usar IDs Opacos Isolados:**  
   Pastas de vídeos devem seguir a nomenclatura canônica `<ID>--<slug>`.

---

## 2. Gates Binários de Auditoria (`video_reengineer.py --audit`)

O comando de auditoria valida 3 gates intransponíveis antes de liberar qualquer entrega:

### GATE 1: Auditoria de Evidências REA (`G-EVIDENCIAS`)
* **Critério:** Todo parágrafo de conclusão técnica em `metodologia.md` deve conter um marcador válido:
  - `[OBSERVADO NO FRAME]`
  - `[DITO NO ÁUDIO]`
  - `[DERIVADO]`
  - `[DESCONHECIDO REA]`
* **Ação se falhar:** O auditor aponta a linha exata sem evidência e reprova a entrega.

### GATE 2: Auditoria de Scaffolding Canônico (`G-SCAFFOLD`)
* **Critério:** Verifica se a pasta segue `<ID>--<slug>` e se as subpastas `raw/`, `transcricao/` e `visual/` contêm seus respectivos artefatos. A raiz só pode conter `manifest.json`, `metodologia.md` e `gap_analysis.md`.
* **Ação se falhar:** Reprova a estrutura e exige limpeza.

### GATE 3: Auditoria de Tracer Bullets (`G-TICKETS`)
* **Critério:** Todo arquivo em `tickets/nano-tickets/*.md` deve conter obrigatoriamente as seções `Target Files`, `Blocked by` e `Validation Command` real.
* **Ação se falhar:** O compilador de tickets barra o avanço da esteira.

---

## 3. Circuit Breakers (Chaves Gerais de Desarme)

Quando um agente de IA ou script detectar uma violação crítica:
1. **Desarme Imediato:** O script interrompe a execução com código de saída diferente de zero (`sys.exit(1)`).
2. **Bloqueio de Commit:** O pre-commit hook ou auditor bloqueia o avanço para a fase de tickets.
3. **Alarme Humano:** O agente para o processamento, reporta ao usuário a regra violada e solicita alinhamento antes de tentar contornar a restrição.
