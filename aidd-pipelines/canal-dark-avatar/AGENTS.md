# AGENTS.md - Governanca para Agentes de IA (Canal Dark Avatar)

Diretrizes para agentes autonomos que executam ou modificam este pipeline.

## 1. Regras Operacionais Inegociaveis
1. Nao altere manualmente os dados em context/handoffs/. Toda transformacao deve ocorrer via runner.
2. Em caso de erro, verifique imediatamente o state.json para obter o codigo e a mensagem do no falho.
3. Toda comunicacao externa deve seguir o padrao universal de handoff definido no ecossistema AIDD.
4. Mantenha os limites de palavras no frontmatter de quaisquer novas micro-skills que forem adicionadas ao pipeline.

## 2. Comandos Operacionais
- Execucao sequencial: `python run_pipeline.py`
- Reexecucao total: `python run_pipeline.py --force`
- Auditoria do estado: leitura de `state.json`
