# RULES.md — Regras de Conformidade e Circuit Breakers (aidd-app-reengineer)

Regras inegociáveis para homologação e execução da esteira.

## Gate 1: Micro-Frontmatter Budget
- A `description` do frontmatter YAML em `SKILL.md` DEVE conter no máximo 25 palavras.

## Gate 2: Padrão Dual-Spec
- Presença obrigatória de `SKILL.md` e `AGENTS.md`.

## Gate 3: Governança Enterprise
- Presença obrigatória de `RULES.md`, `LICENSE` (MIT Heverton Eduardo Peres), `pyproject.toml`, `requirements.txt`, `dependencies.json` e scripts de sincronização `sync.ps1` e `sync.sh`.

## Gate 4: Evidências Mínimas REA
- A dissecação DEVE emitir no mínimo `TOKENS_DESIGN.json`, `conteudo_tecnico.md`, `arquitetura.md`, `MANIFEST_REA.json` e `HANDOFF.json`.
- A violação de qualquer critério desarmará a esteira com status FAILED.
