# Manual de Engenharia &bull; Etapa 1: Entrevista F1

> **Raio-X de Arquitetura da Etapa 1 do Ouroboros**  
> Localização no pipeline: `[1. ENTREVISTA] ➔ 2. SPEC ➔ 3. F2 ORQUESTRAÇÃO ➔ 4. HANDOFF ➔ 5. RUNNER`

---

## 📊 Grau Geral de Automação da Etapa

```
[████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 35% Determinístico | 65% Humano/Agente
```
- **35% Determinístico**: Semente da SPEC (`--from-nl`), schema JSON e limites de frontmatter.
- **65% Humano/Agente**: Interpretação do pedido em linguagem natural, uma pergunta por vez, palpite do agente e **aprovação explícita** (`approved: true`) que só o usuário pode dar.

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| Pedido em linguagem natural | `string` | `"criar app de checklist simples"` | Usuário no chat ou `/ouroboros` |
| `--output-spec` | `Path` | `./SPEC_PIPELINE.json` | CLI (default: cwd) |
| `--goal` | `string` | `"provar fluxo de ponta a ponta"` | CLI / resposta da entrevista |
| Template da SPEC | `JSON` | `schemas/SPEC_PIPELINE.template.json` | Repositório |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 1.1: Reconhecimento do pedido
- **O que faz**: Identifica que o texto é um pedido de fabricação (pipeline/skill a partir de X) e ativa a trilha F1 — não pula para F2.
- **Natureza**: `40% Determinístico / 60% Probabilístico` (heurística simples + julgamento do agente).

### Ação 1.2: Semeadura da SPEC
- **O que faz**: Executa `ouroboros_master.py --from-nl "<pedido>"`, gera `spec_id` (SHA-256) e grava template com `approved: false` e placeholders.
- **Natureza**: `100% Determinístico`.

### Ação 1.3: Entrevista uma pergunta por vez (protocolo interview-me)
- **O que faz**: Pergunta, nesta ordem mínima: alvo (URL/APK/nenhum), sucesso observável, skills (`reuse`/`github-scout`/`create`), nome do pipeline, steps do DAG, instalação de deps. Cada pergunta leva um **palpite**.
- **Natureza**: `10% Determinístico / 90% Humano/Agente`.

### Ação 1.4: Preenchimento e trava de aprovação
- **O que faz**: Escreve as respostas na SPEC; só após confirmação explícita grava `"approved": true`. Placeholders (`PREENCHER`, `placeholder-pipeline`) impedem a F2.
- **Natureza**: `50% Determinístico / 50% Humano` (a trava é sempre humana).

---

## 3. Scripts, Funções e Regras no Código

- **CLI de semente**: `ouroboros.py` &bull; `--from-nl` / `--output-spec` / `--goal`.
- **Script mestre**: `aidd-skills/aidd-ouroboros-master/scripts/ouroboros_master.py` &bull; função `cmd_init_spec`.
- **Template**: `schemas/SPEC_PIPELINE.template.json`.
- **Schema da SPEC**: `schemas/SPEC_PIPELINE.schema.json` (validado na Etapa 3).
- **Skill de conduta**: `aidd-ouroboros-master/SKILL.md` (F1) + skill de harness `interview-me`.
- **Regra de ouro**: F2 proibida sem `approved: true` e sem placeholders.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **SPEC template** | Usuário / Agente | Arquivo JSON: `SPEC_PIPELINE.json` com `approved: false` |
| **SPEC preenchida e aprovada** | Etapa 3 (Validação F2) | Mesmo JSON com `approved: true` e `pipeline.name` real |
| **Resumo da entrevista** | Usuário (humano) | Mensagem no chat (linhas de confirmação) |
| **Pedido original** | Auditoria / F2 | Campo `user_request` + `goal` dentro da SPEC |
