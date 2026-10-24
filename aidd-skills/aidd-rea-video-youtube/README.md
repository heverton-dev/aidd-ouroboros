# AIDD-Video-Reengineer (v1.3.0)

**Skill universal e agnóstica para Engenharia Reversa Metodológica de Vídeos Técnicos do YouTube.**  
Combina o rigor de evidências do **REA (*Reverse Engineer Anything*)** com a modelagem pragmática de domínio do **`aidd-lauren` (*pstack*)**.

---

## 1. O que a Skill Faz

Transforma qualquer vídeo técnico (ou lote de referências internacionais de alto nível) em:
1. **Evidências Primárias:** Transcrição temporal precisa com Whisper + frames congelados via FFmpeg + OCR local determinístico via Tesseract (custo zero de tokens de LLM).
2. **Dissecação Metodológica (`metodologia.md`):** Reconstituição dos prompts mestres, tokens de física/motion design (springs, easing) e pipeline de produção.
3. **Gap Analysis & Adequação (`gap_analysis.md`):** Confronto com sua base de código existente, eliminando complexidade manual (*unslop*).
4. **Nano-Tickets Tracer Bullet:** Backlog de micro-tickets cirúrgicos com critérios de validação automatizados.

---

## 2. Nomenclatura Canônica e Scaffolding Estruturado

Para evitar pastas com IDs opacos ininteligíveis (ex: `Uwpc-z1KppU`), a skill adota o padrão:

```text
research/videos/<VIDEO_ID>--<autor>-<slug-curto>/
```
*Exemplo real:* `research/videos/Uwpc-z1KppU--viktor-kav-animacao-remotion/`

### Scaffolding Interno em 3 Camadas
A raiz da pasta é preservada limpa apenas com os entregáveis executivos:

```text
research/videos/<ID>--<slug>/
├── manifest.json              # [Raiz] Manifesto de evidências REA
├── metodologia.md             # [Raiz] Síntese final da metodologia
├── gap_analysis.md            # [Raiz] Matriz de confronto vs. seu projeto
│
├── raw/                       # [Camada 1: Mídia Bruta / Arquivos Pesados]
│   ├── info.json              # Metadados completos originais da API
│   ├── audio.mp3              # Áudio extraído para transcrição
│   └── video.mp4              # Vídeo baixado em 1080p
│
├── transcricao/               # [Camada 2: Fonética e Parser Heurístico]
│   ├── transcript.txt         # Transcrição contínua com [mm:ss]
│   ├── transcript.tsv         # Tabela precisa com start_s e end_s
│   ├── key_moments.txt        # Trechos ranqueados por densidade técnica
│   └── density_index.json     # Índice de pontuação por palavras-chave
│
└── visual/                    # [Camada 3: Visão e OCR Determinístico]
    ├── prompts_detectados.txt # Telas com código e prompts consolidados
    ├── ocr_evidence.json      # OCR completo de cada frame com pontuação
    └── frames/                # Capturas PNG congeladas para auditoria
```

---

## 3. Contrato Dual-Spec: `SKILL.md` vs. `AGENTS.md`

Esta skill adota a especificação dupla de fronteira (*Dual-Spec*):
* **`SKILL.md`:** Ponto de entrada padrão da indústria de Agent Skills (Claude Code, Antigravity, OpenCode), contendo YAML frontmatter, tabela de portabilidade, gatilhos e gates binários.
* **`AGENTS.md`:** Contrato de governança e invariantes operacionais para harnesses e agentes que procuram diretrizes em Markdown na raiz.

---

## 4. Governança por Gates e Circuit Breakers (`RULES.md`)

A skill implementa a máxima do AIDD: **"Toda regra sem um gate é apenas uma sugestão."**
O comando `--audit` verifica 3 gates binários e desarma a esteira (`sys.exit(1)`) em caso de violação:
* **GATE 1 (`G-EVIDENCIAS`):** Auditoria de marcadores REA em `metodologia.md`.
* **GATE 2 (`G-SCAFFOLD`):** Higiene da nomenclatura canônica e subpastas `raw/`, `transcricao/`, `visual/`.
* **GATE 3 (`G-TICKETS`):** Validação de Tracer Bullets (proibição estrita de stubs).

```bash
python scripts/video_reengineer.py --audit "research/videos/<PASTA_DO_VIDEO>"
```

---

## 5. Como Usar

### Instalação One-Liner Automática (Setup):
```bash
python scripts/video_reengineer.py --setup
```
*(Instala dependências via `uv` ou `pip` e sincroniza com todos os 13 harnesses da máquina).*

### Diagnóstico de Ambiente:
```bash
python scripts/video_reengineer.py --doctor
```

### Dissecação Completa de Vídeo:
```bash
python scripts/video_reengineer.py "https://www.youtube.com/watch?v=Uwpc-z1KppU" --intervalo-frames 10
```

### Auditoria de Conformidade (Gates):
```bash
python scripts/video_reengineer.py --audit "research/videos/Uwpc-z1KppU--viktor-kav-animacao-remotion"
```
