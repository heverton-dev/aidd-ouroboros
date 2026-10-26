# AGENTS.md — Contrato de Governança (aidd-ouroboros-master)

Autor: Heverton Eduardo Peres

1. **F1 antes de F2:** Nunca chame `--orchestrate` sem `approved: true` e spec sem placeholders.
2. **Uma pergunta por vez** na entrevista; sempre com palpite; pare para confirmação explícita.
3. **Determinismo:** Priorize `ouroboros_master.py` e os CLIs canônicos; não reimplemente roteamento/scaffold em texto.
4. **Dúvida na F2:** exit 3 + `pending_question.json` → mini-entrevista → `--resume`. Não improvise.
5. **Proibição ad-hoc:** Skills novas só via `skill_creator.py`; pipelines só via `pipeline_creator.py`.
6. **Gates:** Feche com `ouroboros_master.py --audit` e, se aplicável, `audit_runner.py --skip-pytest`.
