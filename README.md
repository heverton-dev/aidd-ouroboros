# 🐍 AIDD OUROBOROS — A Meta-Fábrica Universal Autônoma

> **Padrão:** AI-Driven Development (AIDD) Canonical Standard  
> **Status:** Ativo / Soberano | **Governança:** Zero Stubs, Strict Determinism, Token Economy, HMAC-SHA256 Integrity

---

## 🌟 O que é o AIDD Ouroboros?

O **AIDD Ouroboros** é uma meta-fábrica autônoma de desenvolvimento orientado a IA capaz de projetar, dissecar, sintetizar e auditar software, pipelines, enxames de agentes (swarms) e produtos digitais completos em loop fechado e contínuo.

Originalmente concebido através do laboratório `stepo`, o Ouroboros transcendeu seu propósito inicial e tornou-se a esteira universal para criação de:
- **Landing Pages & Web Apps** (clone, engenharia reversa e síntese de código limpo).
- **Extensões de Navegador** (Manifest V3 determinístico).
- **Aplicações Full-Stack & APIs** (Python, FastAPI, React, TanStack).
- **Automação Audiovisual & Tutoriais** (Remotion, FFmpeg, Whisper).
- **Novas Skills e Novos Pipelines DAG** sob demanda, em arquitetura de blocos Lego autônomos.

---

## 🏛️ Arquitetura Fractal & Pilares

```
                                      ┌──────────────────────┐
                                      │   AIDD OUROBOROS     │
                                      │ (Meta-Orquestrador)  │
                                      └──────────┬───────────┘
                                                 │
            ┌────────────────────────────────────┼────────────────────────────────────┐
            ▼                                    ▼                                    ▼
┌───────────────────────┐            ┌───────────────────────┐            ┌───────────────────────┐
│     FAMÍLIA REA       │            │  FÁBRICAS DE BLOCOS   │            │  GOVERNANÇA FRACTAL   │
│ (Engenharia Reversa)  │            │ (Skills & Pipelines)  │            │  (Blindagem & Gates)  │
├───────────────────────┤            ├───────────────────────┤            ├───────────────────────┤
│ • rea-router          │            │ • skill-creator       │            │ • gate_ast.py         │
│ • rea-video-youtube   │            │ • pipeline-creator    │            │ • handoff_crypto.py   │
│ • rea-web-saas        │            │ • session-sync        │            │ • audit_runner.py     │
│ • rea-app-android     │            │                       │            │ • Micro-Frontmatter   │
│ • rea-social-carousel │            │                       │            │ • Pointer Passing     │
└───────────────────────┘            └───────────────────────┘            └───────────────────────┘
```

1. **REA Multimodal:** Dissecação profunda de YouTube, sites web, apps Android e postagens sociais.
2. **Economia Extrema de Tokens (Pointer Architecture):** Agentes e nós trocam apenas ponteiros de arquivos e hashes criptográficos HMAC-SHA256, impedindo a degradação de contexto.
3. **Zero Stubs / Zero Mocks:** Código gerado deve ser 100% funcional, tipado e passar no gate AST.
4. **DNA Fractal:** Toda nova peça gerada herda automaticamente suas regras, seu mini-`AGENTS.md` e seus testes negativos/positivos.

---

## 🚀 Instalação Rápida (One-Liner)

### UV (recomendado) — instala o meta-sistema inteiro
```bash
git clone <repo> proj_aidd-ouroboros
cd proj_aidd-ouroboros
# Windows
powershell -ExecutionPolicy Bypass -File setup.ps1
# Linux / macOS
bash setup.sh
```

O `setup.*` detecta `uv` e roda `uv pip install -e .` (console script `ouroboros` + `motores`), sincroniza **todas** as skills (incluindo `aidd-ouroboros-master` → `/ouroboros`) e exporta `AIDD_OUROBOROS_ROOT`.

### Só o pacote (sem sync de harnesses)
```bash
uv pip install -e .
# ou
pip install -e .
ouroboros --master-doctor
```

---

## 🛠️ Comandos Principais

```bash
# Diagnóstico de binários + credenciais
ouroboros --doctor

# Diagnóstico do meta-fluxo (skills + HMAC + motores)
ouroboros --master-doctor

# Quality Gates
ouroboros --audit

# Meta-fluxo: NL → SPEC (F1) → orquestração autônoma (F2)
ouroboros --from-nl "criar pipeline X a partir de https://y"
# ... entrevista; approved=true na SPEC_PIPELINE.json ...
ouroboros --orchestrate ./SPEC_PIPELINE.json --output-dir ./ouroboros-out

# Pipeline existente
ouroboros --pipeline canal-dark-avatar
```

No harness de agentes: skill **`aidd-ouroboros-master`** via `/ouroboros`.

---

## 📁 Estrutura de Diretórios

- `aidd-skills/`: Almoxarifado canônico de micro-skills universais desacopladas.
- `aidd-pipelines/`: DAGs composíveis e executores de enxames de agentes.
- `motores/governanca/`: Guardiões determinísticos (AST Gates, HMAC Cripto, Quality Runner).
- `laboratorio/stepo/`: Casos de estudo e histórico de gestação do ecossistema.
- `tests/`: Suíte automatizada de testes reais.

---

## 📜 Licença

Distribuído sob licença MIT. Copyright (c) 2026 Heverton Eduardo Peres.
