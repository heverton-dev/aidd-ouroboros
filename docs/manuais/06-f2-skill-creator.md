# Manual de Engenharia &bull; Etapa 6: Skill Creator

> **Raio-X de Arquitetura da Etapa 6 do Ouroboros**  
> Localização no pipeline: `5. DISSECAÇÃO ➔ [6. SKILL CREATOR] ➔ 7. PIPELINE CREATOR ➔ 8. DEPS ➔ 9. GATES`

---

## 📊 Grau Geral de Automação da Etapa

```
[███████████████████████████████████░░░░░░░░░░░░░░░] 85% Determinístico | 15% Rede (GitHub)
```
- **85% Determinístico**: Checagem de existência local, scaffold enterprise a partir de templates, auditoria de gates da skill.
- **15% Rede**: GitHub Scout (`gh`/API) com cache e ranking externo — só quando `mode = github-scout` e a skill não existe localmente.

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| `skills_required[]` | `array` | `[{name, role, mode}]` | SPEC (Etapa 1) |
| `mode` | `enum` | `reuse` \| `github-scout` \| `create` | SPEC |
| `github_query` | `string` | `"checklist tdd"` | SPEC (se scout) |
| `--output-dir` | `Path` | `aidd-skills/` do repo | Mestra |
| Cache GitHub | `JSON` | `.cache/github_scout_cache.json` | Disco (TTL 7 dias) |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 6.1: Resolução por reuso
- **O que faz**: Se `aidd-skills/<name>/SKILL.md` existe → `action: reuse`, segue sem criar nada.
- **Natureza**: `100% Determinístico`.

### Ação 6.2: Criação proprietária (mode create)
- **O que faz**: `skill_creator.py --nome <name> --output-dir` gera anatomia enterprise (scripts, references, templates, AGENTS, RULES, sync, dependencies, comandos).
- **Natureza**: `100% Determinístico` (templates fixos).

### Ação 6.3: GitHub Scout (mode github-scout)
- **O que faz**: Busca repositórios por estrelas/licença via `gh` ou REST, usa cache local, refatora no prefixo canônico `aidd-<slug>`.
- **Natureza**: `40% Determinístico / 60% Rede` (resultado depende do GitHub no momento).

### Ação 6.4: Auditoria da skill e registro de estado
- **O que faz**: Roda `--audit` da skill gerada; grava `state.skills[name] = {action, status}`. Falha → exit 3 + `pending_question.json`.
- **Natureza**: `100% Determinístico`.

---

## 3. Scripts, Funções e Regras no Código

- **Função da mestra**: `ouroboros_master.py` &bull; `stage_skills`, `resolve_skill`.
- **Factory**: `aidd-orchestrate-skill-creator/scripts/skill_creator.py` &bull; `create_canonical_skill`, `scout_and_canonize_skill`, `emit_handoff_envelope`.
- **Leis**: micro-frontmatter ≤ 25 palavras; dual-spec SKILL+AGENTS; autocontenção; **prioridade local → GitHub → create**; proibição de criação ad-hoc fora da factory.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **Skills prontas (reuso/novas)** | Etapa 7 (pipeline) e harness (após sync) | Diretórios `aidd-skills/<nome>/` |
| **Estado por skill** | Operador / mestre | `stages.skills` + `state.skills` no state |
| **Handoff da factory** (quando cria) | Downstream | `HANDOFF.json` canônico HMAC na pasta da skill |
| **Dúvida de criação** (exit 3) | Usuário | `pending_question.json` |
