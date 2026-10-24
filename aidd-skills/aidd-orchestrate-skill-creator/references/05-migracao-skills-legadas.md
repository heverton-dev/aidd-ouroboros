# 05 — Migração e Linter de Skills Legadas

O modo `--modo migrate <pasta>` permite atualizar skills antigas para o padrão canônico enterprise:

1. **Diagnóstico da Skill Legada:**
   - Detecta se a skill é composta apenas por um arquivo solto (`SKILL.md`).
   - Verifica se o frontmatter possui mais de 25 palavras.
   - Verifica se faltam `LICENSE`, `RULES.md`, `pyproject.toml` e `sync.ps1`.
2. **Refatoração Automática:**
   - Extrai o corpo do arquivo antigo e move seções longas para `references/`.
   - Gera o Micro-Frontmatter compacto.
   - Cria o scaffolding de 8 pastas e os scripts de auditoria.
   - Preserva toda a lógica original, adicionando a governança enterprise.
