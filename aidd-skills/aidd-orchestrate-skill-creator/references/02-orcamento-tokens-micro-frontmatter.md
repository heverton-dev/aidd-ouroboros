# 02 — Orçamento de Tokens e a Regra do Micro-Frontmatter

## 1. O Problema da Saturação do System Prompt
Harnesses como Claude Code, Antigravity e Cursor leem o frontmatter YAML de **todas as skills instaladas** no início de cada sessão para montar o catálogo de ferramentas disponíveis.

Se o desenvolvedor possui 50 skills, e cada descrição contiver 200 palavras:
- $50 \times 200 = 10.000$ palavras $\approx$ **14.000 tokens consumidos a cada turno de conversa**.
- Isso gera lentidão, custo elevado e degrada o raciocínio do modelo.

## 2. A Solução do Micro-Frontmatter
* A descrição DEVE ter no máximo **25 palavras**.
* Deve listar apenas: papel imperativo + entradas aceitas + saída principal.
* Detalhes, tabelas e explicações longas são empurradas para `references/` e carregadas sob demanda (*Lazy Loading*).
* O script `skill_creator.py --audit` valida matematicamente o número de palavras.
