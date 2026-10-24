# AGENTS.md — Contrato de Governança para Agentes (aidd-pipeline-creator)

Diretrizes para agentes de IA operando o criador de pipelines `aidd-pipeline-creator`.
Autor: Heverton Eduardo Peres

1. **Separação de Papéis:** O agente operando esta skill NUNCA deve criar código de skills inline. Ele orquestra os pipelines, define o DAG (`PIPELINE.json`) e delega a fabricação de novas micro-skills para a `aidd-skill-creator` no Almoxarifado Central (`aidd-skills/`).
2. **Prioridade ao Reuso e Scout:** Antes de criar qualquer pipeline do zero, execute `python scripts/pipeline_creator.py --scout-local` e `--scout-github <termo>` para mapear workflows e pipelines de autoridade existentes.
3. **Pipes e Envelopes Universais:** Toda passagem de dados entre skills deve respeitar o envelope `HANDOFF.json`. Todo pipeline finalizado deve emitir `pipeline_output.json` compatível com a composição de outros pipelines (Lego de Pipelines).
4. **Encapsulamento Canônico:** Pipelines são criados em `aidd-pipelines/<nome>/` com seu próprio runner autônomo, DAG, governança, licença MIT Heverton Eduardo Peres e isolamento de contexto.


