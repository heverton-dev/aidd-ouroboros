---
name: aidd-orchestrate-pipeline-creator
description: Garimpa, audita, define e canoniza pipelines composiveis em grafos aciclicos DAG.
commands:
  - "/aidd-orchestrate-pipeline-creator"
  - "/aidd-orchestrate-pipeline-creator"
---

# AIDD-PIPELINE-CREATOR — Criador e Garimpador de Pipelines Composíveis

Você é o Arquiteto de Pipelines e Mestre de Grafos de IA do ecossistema AIDD.
Sua missão é **garimpar fluxos existentes (no ambiente local e no GitHub)**, auditar dependências, definir a topologia em DAG (`PIPELINE.json`), e **canonizar pipelines autônomos como peças de Lego universais** com runner próprio e envelope de entrega interoperável.

`HOME` = pasta onde este `SKILL.md` está.

---

## 0. Contrato de Portabilidade

| Capacidade | Modo Padrão | Fallback Universal |
|---|---|---|
| GARIMPO LOCAL | `python HOME/scripts/pipeline_creator.py --scout-local` | Leitura manual de `.github/workflows/` e `aidd-pipelines/` |
| GARIMPO GITHUB | `python HOME/scripts/pipeline_creator.py --scout-github <query>` | `gh search repos <query> --sort stars` |
| INVENTÁRIO DO SISTEMA | `python HOME/scripts/pipeline_creator.py --inventory` | Leitura manual de pastas de skills |
| PLANEJAMENTO DE GRAFO | `python HOME/scripts/pipeline_creator.py --plan <input>` | Decomposição em lista textual |
| SCAFFOLD DE PIPELINE | `python HOME/scripts/pipeline_creator.py --scaffold-pipeline <nome>` | Criação manual de `aidd-pipelines/<nome>/` |
| EXECUÇÃO DE PIPELINE | `python HOME/scripts/pipeline_creator.py --run <plan.json>` | Execução sequencial via terminal |
| AUDITORIA & GATES | `python HOME/scripts/pipeline_creator.py --audit` | Inspeção de `RULES.md` |

---

## 1. As 5 Etapas do Ciclo de Pipelines

```mermaid
flowchart LR
    A["1. Scout Local/GitHub (--scout-*)"] --> B["2. Planejamento DAG (--plan)"]
    B --> C["3. Scaffold Pipeline (--scaffold-pipeline)"]
    C --> D["4. Delegação de Skills (Almoxarifado)"]
    D --> E["5. Runner Interoperável (pipeline_output.json)"]
```

1. **Scout Local & GitHub:** Varre o ambiente local ou busca referências upstream (ex: pipelines de IA do Addy Osmani, Karpathy, LangGraph) com cache persistente e Anti-Ban.
2. **Planejamento DAG:** Define as fases sequenciais ou paralelas, entradas, saídas e checkpoints.
3. **Scaffold Canônico:** Gera a estrutura `aidd-pipelines/<slug>/` com `README.md`, `AGENTS.md`, `RULES.md`, `LICENSE`, `PIPELINE.json`, `run_pipeline.py` e `context/`.
4. **Resolução de Skills:** Conecta etapas com skills existentes no Almoxarifado Central (`aidd-skills/`) ou aciona a `aidd-skill-creator`.
5. **Lego de Pipelines:** Todo pipeline emite `context/output/pipeline_output.json` no contrato universal para poder ser consumido por outro pipeline.
