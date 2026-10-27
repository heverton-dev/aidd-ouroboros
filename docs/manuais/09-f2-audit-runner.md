# Manual de Engenharia &bull; Etapa 9: Quality Gates (Audit Runner)

> **Raio-X de Arquitetura da Etapa 9 do Ouroboros**  
> Localização no pipeline: `7. PIPELINE ➔ 8. DEPS ➔ [9. QUALITY GATES] ➔ 10. HANDOFF FINAL`

---

## 📊 Grau Geral de Automação da Etapa

```
[██████████████████████████████████████████████████] 100% Determinístico | 0% Probabilístico
```
- **100% Determinístico**: AST, contagem de palavras, checagens de filesystem e baseline — mesma árvore de código ⇒ mesmo resultado.

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| Raiz do repositório | `Path` | cwd ou `AIDD_OUROBOROS_ROOT` | Ambiente |
| `--skip-pytest` | `bool` | presente na F2 | Mestra / CLI |
| Baseline de violações | `JSON` | `motores/governanca/gate_baseline.json` | Repo |
| Código, skills, pipelines | filesystem | `aidd-skills/**`, `aidd-pipelines/**` | Repo |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 9.1: Gate AST / Zero-stubs
- **O que faz**: Varre `.py` com `gate_ast.py`; reprova sintaxe inválida e `except: pass` / stubs, respeitando `gate_baseline.json`.
- **Natureza**: `100% Determinístico`.

### Ação 9.2: Gate Micro-frontmatter
- **O que faz**: `description` de cada `SKILL.md` ≤ 25 palavras.
- **Natureza**: `100% Determinístico`.

### Ação 9.3: Gate AGENTS.md fractal
- **O que faz**: Existe e respeita limite de palavras do projeto.
- **Natureza**: `100% Determinístico`.

### Ação 9.4: Gate anatômico (Circuit Breaker)
- **O que faz**: Reprova skills/pipelines anêmicos (ex.: `templates/` vazio = criação ad-hoc).
- **Natureza**: `100% Determinístico`.

### Ação 9.5: Pytest (opcional)
- **O que faz**: Em F2 costuma vir `--skip-pytest`; no CI/`ouroboros --audit` completo roda a suíte.
- **Natureza**: `100% Determinístico` (execução local).

---

## 3. Scripts, Funções e Regras no Código

- **Função da mestra**: `ouroboros_master.py` &bull; `stage_audit`.
- **Orquestrador**: `motores/governanca/audit_runner.py`.
- **AST**: `motores/governanca/gate_ast.py` &bull; `scan_path`, baseline.
- **Regras do projeto**: zero stubs; micro-frontmatter; governança fractal; anatomia enterprise obrigatória.
- **Estado F2**: rc=0 → `stages.audit=OK` e F2 pode fechar SUCCESS; rc≠0 → F2 PARTIAL / exit 1.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **Veredito dos gates** | Mestra / CI / operador | Exit code 0 ou 1 + log `[OK]`/`[FALHA]` em stdout |
| **Estado do gate** | Handoff final (Etapa 10) | `stages.audit = {status, rc}` → define SUCCESS vs PARTIAL |
| **Evidência de conformidade** | Revisor humano / auditoria | Relatório textual da execução do `audit_runner` |
