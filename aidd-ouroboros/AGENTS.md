# AGENTS.md — Governanca para Agentes de IA (aidd-ouroboros)

Diretrizes inegociaveis para agentes de IA que operam ou mantem o Meta-Pipeline Ouroboros.

## 1. Leis de Governanca Operacional
1. Nunca execute acoes destructivas fora do diretorio do projeto. Toda criacao deve respeitar as fronteiras do ecossistema.
2. Toda passagem de dados entre estagios deve obrigatoriamente validar o payload contra os schemas presentes em schemas/.
3. Ao gerar novas skills a partir do ciclo, utilize sempre a fábrica canonica aidd-skill-creator.
4. Ao orquestrar mais de duas skills, provisione sempre um pipeline encapsulado via aidd-skill-swarm. Nunca deixe skills avulsas na raiz.
5. Em caso de falha de execucao, o agente DEVE consultar state.json antes de propor correcoes manuais.

## 2. Roteamento de Comandos
- Iniciar ciclo completo: `python run_ouroboros.py --input <fonte>`
- Validar conformidade: `python run_ouroboros.py --audit`
- Diagnostico de sistema: `python run_ouroboros.py --doctor`
