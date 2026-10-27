# Manual de Engenharia &bull; Etapa 11: Runner do Pipeline Gerado

> **Raio-X de Arquitetura da Etapa 11 do Ouroboros**  
> Localização no pipeline: `1..10 F2 (FABRICAÇÃO) ➔ [11. RUNNER] ➔ entrega em execução`

---

## 📊 Grau Geral de Automação da Etapa

```
[███████████████████████████████████░░░░░░░░░░░░░░░] 90% Determinístico | 10% Skills/Rede
```
- **90% Determinístico**: Ordenação topológica, `inputs_hash`, máquina de estados do workspace, resolução de entrypoints via `cli_contract`.
- **10% Skills/Rede**: O que cada skill faz de fato (REA web usa rede; scaffold é local). Limitação conhecida: nós com inputs placeholder podem concluir em “modo help”.

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| `PIPELINE.json` | `JSON` | `OUT/aidd-pipelines/<slug>/PIPELINE.json` | Etapa 7 |
| `--workspace` | `Path` | `/tmp/ws` | CLI (ou `.workspaces/run_*`) |
| `--force` / `--resume` | `bool` / `run_id` | reexecuta / retoma | CLI |
| `AIDD_OUROBOROS_ROOT` | `env` | raiz do repo com `aidd-skills/` | Ambiente (recomendado fora de `aidd-pipelines/` raiz) |
| Skills | `dependencies.json` | entrypoint + `cli_contract` | `aidd-skills/<nome>/` |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 11.1: Resolução da raiz do repositório
- **O que faz**: Procura `AIDD_OUROBOROS_ROOT` → `pipeline.parent.parent` → `cwd` e pais; primeira pasta com `aidd-skills/`.
- **Natureza**: `100% Determinístico`.

### Ação 11.2: Ordenação topológica do DAG
- **O que faz**: Ordena por `depends_on`; detecta ciclo → erro.
- **Natureza**: `100% Determinístico`.

### Ação 11.3: Controle de estado e cache de inputs
- **O que faz**: `state.json` por `run_id`; `inputs_hash` (SHA-256 do input + estrutura do nó); nó COMPLETED com hash igual e sem `--force` → skip.
- **Natureza**: `100% Determinístico`.

### Ação 11.4: Resolução e execução do nó
- **O que faz**: Lê `entrypoint` e `cli_contract.input_flag/output_flag`; monta comando; `subprocess` com cwd/workspace; rc≠0 → FAILED e aborta.
- **Natureza**: `95% Determinístico / 5% Mistura` (depende da skill invocada).

### Ação 11.5: Fecho do workspace
- **O que faz**: Todos OK → `state.status = COMPLETED`, exit 0.
- **Natureza**: `100% Determinístico`.

---

## 3. Scripts, Funções e Regras no Código

- **Template**: `aidd-orchestrate-pipeline-creator/templates/RUN_PIPELINE_TEMPLATE.py`.
- **Funções**: `resolve_repo_root`, `resolve_skill_execution`, `topological_sort`, `execute_pipeline`.
- **Regras**: contrato `dependencies.json` + `cli_contract`; sem globbing de `*.py`; zero stubs; handoffs de nó quando a skill emite.
- **Contrato de testes**: `tests/test_entrypoints.py` garante entrypoint e flags existentes em todas as skills canônicas.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **Estado da execução** | Operador / CI | `WORKSPACE/state.json` (`COMPLETED`/`FAILED`) |
| **Saídas por nó** | Downstream / humano | `WORKSPACE/<node_id>/` |
| **Código de saída** | Shell / pipeline de deploy | Exit 0 = todos os nós OK |
| **Evidência de DAG real** | Teste E2E | Ex.: `aidd-pipelines/_e2e-smoke` com HMAC por nó |

> **Nota de operação:** a fabricação (F2) e a execução (runner) são separadas. O trabalho pesado de ponta a ponta comprovado hoje: **F2 da mestra** + runners com inputs reais (`_e2e-smoke`).
