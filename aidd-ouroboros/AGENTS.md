# AGENTS.md — Governanca para Agentes de IA (aidd-ouroboros)

Diretrizes inegociaveis para agentes de IA que operam ou mantem o Meta-Pipeline Ouroboros.

## 1. Leis de Governanca Operacional
1. Nunca execute acoes destructivas fora do diretorio do projeto. Toda criacao deve respeitar as fronteiras do ecossistema.
2. Toda passagem de dados entre estagios deve obrigatoriamente validar o payload contra os schemas presentes em schemas/.
3. Ao gerar novas skills a partir do ciclo, utilize sempre a fabrica canonica `aidd-orchestrate-skill-creator`.
4. Ao orquestrar mais de duas skills, provisione sempre um pipeline encapsulado via `aidd-orchestrate-pipeline-creator`. Nunca deixe skills avulsas na raiz.
5. Em caso de falha de execucao, o agente DEVE consultar state.json antes de propor correcoes manuais.

## 2. Roteamento de Comandos (entrypoint unificado: raiz)
- Diagnostico global: `ouroboros --doctor` (ou `python ouroboros.py --doctor`)
- Auditoria de gates: `ouroboros --audit`
- Meta-fluxo F1/F2: `ouroboros --from-nl "..."` → spec → `ouroboros --orchestrate SPEC.json`
- Ciclo de video: `python aidd-ouroboros/run_ouroboros.py --video <url>` (despacha `aidd-rea-router`)
