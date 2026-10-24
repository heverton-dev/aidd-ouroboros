# AIDD-Pipeline-Creator (v1.0.0)

**Criador e Garimpador de Pipelines Composíveis (Lego de Pipelines).**  
Criada por **Heverton Eduardo Peres** sob o padrão AIDD / REA + `aidd-lauren`.

---

## 1. Visão Geral

A `aidd-pipeline-creator` é a camada de **Engenharia e Composição de Pipelines** do ecossistema AIDD. 
Ela realiza o garimpo de fluxos no ambiente local do usuário e no GitHub (ex: pipelines de IA do Addy Osmani, Karpathy e LangGraph), audita os nós, gera a topologia acíclica dirigida (`PIPELINE.json`) e encapsula tudo em pipelines executáveis de alta governança em `aidd-pipelines/<slug>/`.

Além disso, todo pipeline gerado é uma **peça de Lego composível**, emitindo um envelope universal `pipeline_output.json` para encadeamento em Macro-Pipelines (Meta-Fábricas).

---

## 2. Capacidades Principais

* **Scout Local (`--scout-local`):** Garimpa workflows existentes em `.github/workflows/`, `aidd-pipelines/` e scripts orquestradores na máquina.
* **Scout GitHub (`--scout-github`):** Garimpa repositórios e workflows de autoridade no GitHub com cache persistente e Anti-Ban Circuit Breaker.
* **Environment Discovery (`--inventory`):** Mapeia todas as skills instaladas nas 13 harnesses da máquina e no Almoxarifado Central (`aidd-skills/`).
* **Scaffold Canônico (`--scaffold-pipeline`):** Gera pipelines isolados e prontos para execução contendo `README.md`, `AGENTS.md`, `RULES.md`, `LICENSE`, `PIPELINE.json`, `run_pipeline.py` e contextos de dados.
* **Resolução DRY:** Conecta os passos do pipeline diretamente com as skills do Almoxarifado Central (`aidd-skills/`) sem duplicar código.

---

## 3. Como Usar

### Garimpar Pipelines no Ambiente Local:
```bash
python scripts/pipeline_creator.py --scout-local
```

### Garimpar Pipelines de Autoridade no GitHub:
```bash
python scripts/pipeline_creator.py --scout-github "addyosmani ai workflow"
```

### Criar Scaffold de Novo Pipeline:
```bash
python scripts/pipeline_creator.py --scout-and-canonize "meu-pipeline" --steps "aidd-video-reengineer,aidd-dark-storycraft,aidd-video-materializer"
```

### Sincronização Universal Multi-Harness:
```powershell
powershell -File sync.ps1
```
