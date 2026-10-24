# RULES.md — Regras de Conformidade e Circuit Breakers (aidd-rea-router)

Regras inegociáveis para homologação e execução da esteira.

## Gate 1: Micro-Frontmatter Budget
- A `description` do frontmatter YAML em `SKILL.md` DEVE conter no máximo 25 palavras.

## Gate 2: Padrão Dual-Spec
- Presença obrigatória de `SKILL.md` e `AGENTS.md`.

## Gate 3: Governança Enterprise
- Presença obrigatória de `RULES.md`, `LICENSE` (MIT Heverton Eduardo Peres), `pyproject.toml`, `requirements.txt`, `dependencies.json` e scripts de sincronização `sync.ps1` e `sync.sh`.

## Gate 4: Roteamento Determinístico nos Scripts
- O script principal DEVE implementar `--route` (ou `--target`), `--classify`, `--doctor` e `--audit`.
- A violação de qualquer critério desarmará a esteira com status FAILED.
