# 01 — Protocolo de Interrogatório Socrático (Grill)

O modo `--modo socratic` conduz uma entrevista cirúrgica antes de gerar qualquer arquivo. O objetivo é eliminar ambiguidades e evitar skills genéricas.

## As 5 Perguntas Canônicas
1. **Missão Imperativa:** Qual é a tarefa exata e atômica que a skill executa?
2. **Entradas & Saídas:** O que ela recebe (URL, arquivo, texto) e o que entrega em disco?
3. **Guardrails Negativos:** Quais são as 3 coisas que a skill NUNCA deve fazer?
4. **Ferramental Determinístico Local:** Quais binários, scripts ou pacotes ela usa para ter custo zero de tokens em tarefas mecânicas?
5. **Critério Binário de Sucesso:** Como um auditor automatizado sabe se a execução passou ou falhou?

Ao final da entrevista, o agente compila `SPEC_SKILL.json` e só avança após a aprovação humana.
