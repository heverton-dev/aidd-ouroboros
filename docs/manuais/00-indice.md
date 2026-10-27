# Manual de Engenharia • Visão Geral: Meta-Fluxo Ouroboros

> **Raio-X de Arquitetura do Ouroboros (Todas as Etapas)**  
> Localização no pipeline: `[1. F1 ENTREVISTA] ➔ 2. SPEC ➔ 3. F2 ORQUESTRAÇÃO ➔ 4. HANDOFF ➔ 5. RUNNER`

---

## 📊 Grau Geral de Automação do Sistema

```
[██████████████████████████████░░░░░░░░░░░░░░░░░░░] 60% Determinístico | 40% Misto
```
- **60% Determinístico**: Validação de SPEC (JSON Schema), roteamento REA, scaffold de pipelines, instalação de deps, quality gates AST, assinatura HMAC-SHA256 e runner de DAG.
- **40% Misto**: Entrevista F1 (julgamento do agente + decisão humana), interpretação de NL, captura de rede na dissecação e scout GitHub (rede + ranking externo).

---

## 1. Índice das Etapas

| # | Manual | Fase | Natureza dominante |
| :--- | :--- | :--- | :--- |
| 01 | [Entrevista F1](01-f1-entrevista.md) | F1 | Humano + Agente |
| 02 | [Semeadura da SPEC](02-f1-semeadura-spec.md) | F1 | 100% Determinístico |
| 03 | [Validação da SPEC](03-f2-validacao-spec.md) | F2 | 100% Determinístico |
| 04 | [Roteamento REA](04-f2-rea-router.md) | F2 | 100% Determinístico |
| 05 | [Dissecação REA](05-f2-dissecao-rea.md) | F2 | 70% Det. / 30% Rede |
| 06 | [Skill Creator](06-f2-skill-creator.md) | F2 | 85% Det. / 15% Rede |
| 07 | [Pipeline Creator](07-f2-pipeline-creator.md) | F2 | 100% Determinístico |
| 08 | [Dependency Resolver](08-f2-dependency-resolver.md) | F2 | 60% Det. / 40% Ambiente |
| 09 | [Quality Gates](09-f2-audit-runner.md) | F2 | 100% Determinístico |
| 10 | [Handoff Final](10-f2-handoff-final.md) | F2 | 100% Determinístico |
| 11 | [Runner do Pipeline](11-runner-pipeline.md) | Pós-F2 | 90% Det. / 10% Skills |

---

## 2. Fluxo em Uma Linha

**Pedido NL** → Entrevista (aprovação humana) → **SPEC.json** → F2 autônoma: valida → REA (se houver alvo) → skills → scaffold → deps → audit → **handoff HMAC** → runner do DAG.

---

## 3. Convenções de Nomenclatura

| Conceito | Significado |
| :--- | :--- |
| **F1** | Fase interativa (entrevista + SPEC) |
| **F2** | Fase autônoma (`--orchestrate`) |
| **Exit 0/1/2/3** | Sucesso / Erro técnico / Não aprovado / Dúvida (mini-entrevista) |
| **Determinístico** | Mesmo input → mesmo output, sem LLM |
| **Probabilístico** | Depende de LLM, julgamento ou rede externa |

---

## 4. O que o Sistema Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **SPEC aprovada** | F2 (orquestrador) | Arquivo JSON: `SPEC_PIPELINE.json` com `approved: true` |
| **Pipeline canônico** | Usuário / Runner | Pasta: `OUT/aidd-pipelines/<nome>/` com DAG + runner |
| **Handoffs assinados** | Auditoria / próximo nó | JSON HMAC-SHA256: `OUT/handoffs/*.json` |
| **Relatório de gates** | CI / operador | Exit code 0 do `audit_runner` + log em stdout |
