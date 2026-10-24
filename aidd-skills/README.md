# AIDD-SKILLS — Almoxarifado Central de Micro-Skills

Repositorio canonico e Single Source of Truth (SSOT) de todas as micro-skills universais do ecossistema AIDD.
Autor: Heverton Eduardo Peres (2026)

## 1. Visao Geral
Todas as micro-skills desenvolvidas ou refatoradas no ecossistema AIDD residem neste diretorio. Elas sao estritamente especializadas (Filosofia Unix: faca uma unica coisa com excelencia), autocontidas e universais.

## 2. Inventario do Almoxarifado

| Skill | Responsabilidade Tecnica | Dual-Spec | Micro-Frontmatter |
| :--- | :--- | :---: | :---: |
| `aidd-video-reengineer` | Dissecacao REA de videos (audio, frames, OCR e metadados) | Sim | 18 palavras |
| `aidd-skill-creator` | Fabrica autonoma de novas skills com governanca e gates | Sim | 21 palavras |
| `aidd-skill-swarm` | Mestre de obras, mapeamento de dependencias e construtor de DAG | Sim | 21 palavras |
| `aidd-dark-storycraft` | Roteirizacao e transcriacao cultural para canais dark | Sim | 11 palavras |
| `aidd-remotion-motion` | Gerador procedural de animacoes a 60fps com fisica de molas | Sim | 13 palavras |
| `aidd-video-materializer` | Sintetizador de voz neural e compositor audiovisual MP4 | Sim | 11 palavras |
| `aidd-tutorial-creator` | Maestro de tutoriais de plataformas web e mobile | Sim | 21 palavras |

## 3. Sincronizacao Global com os 13 Harnesses
Para sincronizar todas as skills deste almoxarifado em todas as pastas de configuracao do seu computador:

No Windows (PowerShell):
```bash
powershell -ExecutionPolicy Bypass -File aidd-skills/sync_all.ps1
```

No Linux / macOS (Bash):
```bash
bash aidd-skills/sync_all.sh
```

## 4. Reuso em Pipelines (Zero Duplicacao)
Os pipelines em `aidd-pipelines/` nao duplicam os arquivos das skills. Eles referenciam diretamente as pastas deste almoxarifado central, garantindo que qualquer aprimoramento em uma skill beneficie imediatamente todos os pipelines dependentes.
