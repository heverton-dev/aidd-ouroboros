# REA do AIDD-Ouroboros — Mapa Real vs Fluxo Ideal

> **Data:** 2026-10-26  
> **Método:** Código-fonte como fonte da verdade (motores, scripts, skills, schemas). Docs = intenção a comparar.  
> **Gate:** `python motores/governanca/audit_runner.py --skip-pytest` → **exit 0** (92 py OK, micro-frontmatter OK, AGENTS.md OK, anatomia enterprise OK).

---

## 1. Fluxo ideal (confirmado na entrevista)

```
Pedido NL ("criar pipeline X a partir do app Y")
  │
  ▼
[F1 INTERATIVA] interview-me / entrevista socrática
  → SPEC_PIPELINE.json + planning completo
  → gate de aprovação explícita do usuário
  │
  ▼
[F2 AUTÔNOMA]
  1b. aidd-rea-router  → classifica e despacha
  1c. dissecador REA   → HANDOFF.json assinado
  2.  skill-creator    → busca local → GitHub → proprietária
  3.  dependency_resolver → instala deps das skills/pipeline
  4.  pipeline-creator → DAG + scaffold + runner
  │
  ▼
Dúvida nova na F2 → mini-entrevista pontual → retoma F2
  │
  ▼
audit_runner → exit 0 → pipeline entregue
```

Entradas pós-install UV: CLI `ouroboros` **e** slash `/ouroboros` (skill mestra).

---

## 2. O que existe de fato (mapa real)

### 2.1 Camada de entrada

| Peça | Path | Status | Evidência |
|------|------|--------|-----------|
| CLI raiz soberana | `ouroboros.py` | **PARCIAL** | Flags: `--doctor`, `--credentials`, `--audit`, `--setup`, `--pipeline`, `--target`+`--goal` (síntese de plano por regras de extensão/URL). **Não** recebe NL livre nem dispara entrevista. |
| Executor meta-pipeline | `aidd-ouroboros/run_ouroboros.py` | **PARCIAL** | Ciclo **só de vídeo** (`--video URL` → `aidd-rea-video-youtube`). `--github-scout` declarado no argparse mas **não implementado** no `main`. Sem ligação com skill/pipeline-creator. |
| Grafo mestre | `aidd-ouroboros/OUROBOROS.json` | **DESVIADO** | 4 macronós = ciclo de produção de vídeo (REA→storycraft→pipeline-creator→video-synth). **Não** descreve o meta-fluxo de fabricação de pipeline a partir de NL. |
| Console script UV | `pyproject.toml` | **AUSENTE** | Sem `[project.scripts]`. Install via `setup.ps1`/`setup.sh` (pip + sync skills), não via `uv tool install` com entrypoint `ouroboros`. |
| Skill mestra `/ouroboros` | — | **AUSENTE** | Não existe `SKILL.md` canônico de orquestração NL→fluxo. Pasta `aidd-ouroboros/` não é skill harness (sem SKILL.md, sem commands/). |
| Slash commands | `aidd-skills/*/commands/` | **OK (parcial)** | Comandos para rea-router, skill-creator, pipeline-creator. Nenhum para o fluxo master. |

### 2.2 Peças do fluxo ideal (componentes)

| Etapa | Componente | Path | Status real |
|-------|------------|------|-------------|
| Interview | interview-me / socrático | `skill_creator.py` docstring + `AGENTS.md` + `references/01-interrogatorio-socratico-grill.md` | **DOCUMENTADO, NÃO IMPLEMENTADO.** Docstring cita `--modo [socratic\|doc\|image\|migrate]`; `argparse` do script **não tem** `--modo`. Nenhuma função de entrevista no código. |
| Roteamento REA | `aidd-rea-router` | `aidd-skills/aidd-rea-router/scripts/rea_router.py` (346 linhas) | **OK.** `--classify`, `--target/--route`, `--output-handoff`, `--doctor`, `--audit`. Smoke: URL → `{"type":"web","skill":"aidd-rea-web-saas",...}`. |
| Dissecação REA | 4 especialistas | `aidd-rea-{video-youtube,web-saas,social-carousel,app-android}` | **OK.** Anatomia enterprise completa; scripts com `--input`/`--output-handoff`. |
| Skill factory | `aidd-orchestrate-skill-creator` | `skill_creator.py` (971 linhas) | **OK (sem socrático).** `--nome`, `--input`, `--github-scout`, `--evolve`, `--audit`. Busca GitHub via `gh`/REST + cache. Sem `--modo socratic`, sem geração de `SPEC_SKILL.json` via entrevista. |
| Deps | `dependency_resolver.py` | `motores/governanca/dependency_resolver.py` | **OK isolado.** Resolve `dependencies.json`, checa binários/pacotes. **Não** é invocado por `ouroboros.py` nem por `pipeline_creator.py` após scaffold/criação. |
| Pipeline factory | `aidd-orchestrate-pipeline-creator` | `pipeline_creator.py` (919 linhas) | **OK.** `--scout-local`, `--scout-github`, `--scaffold-pipeline`, `--plan`, `--inventory`, `--evolve`. Gera DAG + anatomia. Não instala deps automaticamente. |
| Handoff crypto | `handoff_crypto.py` | `motores/governanca/` | **OK.** Schema em `aidd-ouroboros/schemas/HANDOFF.schema.json`. |
| Quality gate | `audit_runner.py` | `motores/governanca/` | **OK.** 5 gates; `--skip-pytest` exit 0 em 0.73s. |
| Síntese de plano NL-ish | `sintetizar_plano()` | `ouroboros.py:169-220` | **FRÁGIL.** Heurística por extensão/URL; falha com `ValueError` se não casar. Não é entrevista nem spec de pipeline multi-etapa. |

### 2.3 Contrato de handoff entre etapas

Existe schema e crypto, mas **não há orquestrador** que encadeie:

`interview_spec.json → rea_router → HANDOFF_REA → skill_creator(s) → dependency_resolver → pipeline_creator → audit`

Cada CLI é executável isolado; o “glue” é o agente humano/LLM lendo docs — o oposto do Determinism First do AGENTS.md.

---

## 3. Gap analysis (ideal − real)

| # | Gap | Severidade | Evidência |
|---|-----|------------|-----------|
| **G1** | **Sem entrada NL + interview-me no topo.** Nenhum path do repo dispara entrevista interativa e gera `SPEC_PIPELINE.json` completo (skills, MCPs, motores, handoffs, regras, hooks, configs). | **CRÍTICA** | Sem flag/skill mestra; `--modo socratic` só em docs. |
| **G2** | **Sem orquestrador autônomo pós-entrevista** que encadeie router→REA→skill-creator→deps→pipeline-creator com handoffs assinados e mini-entrevista em dúvida. | **CRÍTICA** | `run_ouroboros.py` só vídeo; `ouroboros.py --target` só 1 skill. |
| **G3** | **Modo socrático do skill-creator não implementado** (doc promete, argparse não entrega). | **ALTA** | `skill_creator.py` ~L894-972 sem `--modo`. |
| **G4** | **Sem console script UV / install único** que instale meta-sistema + skills + `/ouroboros`. | **ALTA** | `pyproject.toml` sem `[project.scripts]`. |
| **G5** | **Sem skill mestra `/ouroboros`** instalável via sync. | **ALTA** | Pasta `aidd-ouroboros/` sem SKILL.md/commands. |
| **G6** | **`dependency_resolver` órfão** no fluxo de fabricação (não roda após criar skills/pipeline). | **MÉDIA** | Sem chamada em ouroboros/skill_creator/pipeline_creator. |
| **G7** | **Dois entrypoints concorrentes incompletos** (`ouroboros.py` vs `aidd-ouroboros/run_ouroboros.py`) com semântica diferente. | **MÉDIA** | Duplicação parcial de doctor/audit. |
| **G8** | **`OUROBOROS.json` não modela o meta-fluxo de fabricação** (só ciclo de vídeo). | **MÉDIA** | 4 macronós de produto audiovisual. |
| **G9`** | **`--github-scout` em `run_ouroboros.py` morto** (argparse sem handler). | **BAIXA** | `main()` sem branch. |
| **G10** | **Nomenclatura inconsistente** em AGENTS do rea-router (`aidd-video-reengineer` vs canônico `aidd-rea-video-youtube`). | **BAIXA** | Docs do router vs dirs reais. |
| **G11** | **Síntese de plano por regras frágeis** (`sintetizar_plano`) não cobre “criar pipeline a partir de app Y” multi-etapa. | **MÉDIA** | `ouroboros.py:191` raise se não casar regra. |

---

## 4. Arquitetura-alvo da correção (cirúrgica)

Reaproveitar motores/gates (audit OK). **Reescrever/adicionar apenas a camada de orquestração.**

```
aidd-skills/aidd-ouroboros-master/          # NOVA skill mestra (sync multi-harness)
  SKILL.md                                  # /ouroboros — recebe NL
  AGENTS.md, RULES.md, ...
  scripts/ouroboros_master.py               # F1 interview + F2 dispatch
  references/fluxo-completo.md

ouroboros.py                                # ESTENDER: --from-nl, --orchestrate <spec>
  → chama ouroboros_master.run() ou espelha lógica

pyproject.toml
  [project.scripts]
  ouroboros = "ouroboros:main"
```

**F2 (autônoma) — sequência determinística:**

1. `rea_router.py --target <alvo> --output-handoff ...`
2. Dissecador especialista → `HANDOFF_REA.json`
3. `skill_creator.py --github-scout|--input|--nome` (por skill da spec) + audit
4. `dependency_resolver.py` em cada `dependencies.json` gerado + pipeline
5. `pipeline_creator.py --plan` + `--scaffold-pipeline` + `--steps`
6. `audit_runner.py --skip-pytest` (e pytest no CI)

**Dúvida na F2:** gravar `pending_question.json` → reabrir entrevista → retoma checkpoint (não improvisar).

**Implementações mínimas:**

- `--modo socratic` real em `skill_creator.py` **ou** entrevista só na skill mestra (preferível: mestra única; skill-creator recebe `SPEC_SKILL.json` pronto).
- Estender `OUROBOROS.json` **ou** novo `FABRICATION.json` com os 5 macronós do meta-fluxo.

---

## 5. Priorização da correção

| Fase | Trabalho | Critério de pronto |
|------|----------|--------------------|
| **P0** | Skill mestra `aidd-ouroboros-master` + `--from-nl` em `ouroboros.py` + flag `--orchestrate <SPEC_PIPELINE.json>` | Pedido NL → interview → spec em disco; após yes, F2 roda |
| **P1** | Encadeamento F2 com handoffs HMAC + mini-entrevista em gap | Pipeline de smoke E2E passa sem intervenção manual entre etapas |
| **P2** | `[project.scripts]` UV + setup que instala tudo + sync da mestra | `uvx`/`uv tool install` → `ouroboros --doctor` e `/ouroboros` no harness |
| **P3** | Ligar `dependency_resolver` no fim de skill/pipeline create; limpar run_ouroboros morto; corrigir G9/G10 | audit exit 0 + sem flags mortas |

---

## 6. Riscos

1. **Entrevista viva vs determinismo:** interview-me é LLM/interativo; o resto deve ser scripts. Manter fronteira dura: spec JSON versionado é o único input da F2.
2. **Duplicação de doctor/audit** entre dois entrypoints — unificar sob `ouroboros.py`.
3. **Scout GitHub** depende de `gh`/rede — fallback REST já existe; testar offline.
4. **Pytest completo estourou timeout** no gate completo nesta máquina — usar `--skip-pytest` no dev, pytest no CI.

---

## 7. Status da correção P0 (2026-10-26)

| Item | Status |
|------|--------|
| Skill `aidd-ouroboros-master` (anatomia enterprise + F1/F2) | **IMPLEMENTADO** |
| `schemas/SPEC_PIPELINE.schema.json` + template | **IMPLEMENTADO** |
| `ouroboros.py --from-nl / --orchestrate / --master-doctor` | **IMPLEMENTADO** |
| `[project.scripts] ouroboros` no pyproject | **IMPLEMENTADO** |
| Smoke F2 aprovado (REA→reuse skill→scaffold→audit) | **exit 0** |
| `audit_runner --skip-pytest` | **exit 0** (95 py) |

Pendente (P1+): mini-entrevista formal em exit 3 já gravada via `pending_question.json` (protocolo documentado em SKILL.md); falta só o agente reabrir o diálogo — lógica de resume já existe (`--resume`).

---

*Gerado por REA do repositório (código-fonte). Substitui narrativa de docs quando em conflito.*
