# Manual de Engenharia &bull; Etapa 7: Pipeline Creator (Scaffold)

> **Raio-X de Arquitetura da Etapa 7 do Ouroboros**  
> Localização no pipeline: `6. SKILLS ➔ [7. PIPELINE CREATOR] ➔ 8. DEPS ➔ 9. GATES ➔ 10. HANDOFF`

---

## 📊 Grau Geral de Automação da Etapa

```
[██████████████████████████████████████████████████] 100% Determinístico | 0% Probabilístico
```
- **100% Determinístico**: Scaffold a partir de templates + reescrita do `PIPELINE.json` com o DAG exato da SPEC. Sem rede e sem LLM nesta etapa.

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| `pipeline.name` | `string` | `"e2e-real"` | SPEC (Etapa 1) |
| `pipeline.steps[]` | `array` | `[{id, skill, depends_on}]` | SPEC |
| `--output-dir` | `Path` | `OUT/` (cwd do scaffold) | Mestra |
| Skills referenciadas | `nomes` | `aidd-rea-web-saas` | Etapa 6 / Almoxarifado |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 7.1: Validação do DAG mínimo
- **O que faz**: Exige `name` e `steps` com pelo menos um `skill` válido. Sem isso → exit 3.
- **Natureza**: `100% Determinístico`.

### Ação 7.2: Scaffold canônico
- **O que faz**: `pipeline_creator.py --scaffold-pipeline <nome> --steps <csv-de-skills>` cria `OUT/aidd-pipelines/<slug>/` com README, AGENTS, RULES, LICENSE, PIPELINE.json, state.json, run_pipeline.py, context/, templates/, references/.
- **Natureza**: `100% Determinístico`.

### Ação 7.3: Reescrita rica do DAG
- **O que faz**: Sobrescreve `PIPELINE.json` com IDs, descrições e `depends_on` originais da SPEC (o CSV do CLI só aciona o scaffold).
- **Natureza**: `100% Determinístico`.

### Ação 7.4: Publicação no state da F2
- **O que faz**: `stages.pipeline = {status: OK, path: <dir>}`. Path ausente pós-scaffold → exit 3.
- **Natureza**: `100% Determinístico`.

---

## 3. Scripts, Funções e Regras no Código

- **Função da mestra**: `ouroboros_master.py` &bull; `stage_pipeline`.
- **Factory**: `pipeline_creator.py` &bull; `scaffold_autonomous_pipeline`, CLI `--scaffold-pipeline`.
- **Regras**: anatomia enterprise completa (circuit breaker); encapsulamento em pasta própria; nunca skills soltas na raiz; runner padrão de `templates/RUN_PIPELINE_TEMPLATE.py`.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **Pipeline encapsulado** | Operador + Etapa 8 (deps) + Etapa 11 (runner) | Pasta `OUT/aidd-pipelines/<slug>/` |
| **DAG canônico** | Runner / humanos | `PIPELINE.json` com nós e `depends_on` |
| **Runner** | Execução pós-F2 | `run_pipeline.py` (+ `state.json` INITIALIZED) |
| **Estado F2** | Mestra | `stages.pipeline.status = "OK"` |
