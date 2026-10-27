# Manual de Instrucoes: e2e-hmac

Pipeline autonomo composivel e deterministico criado pelo aidd-pipeline-creator.

## 1. Visao Geral
Este pipeline automatiza a cadeia de execucao completa para e2e-hmac.
Opera como uma **peca de Lego composivel**, consumindo `context/input/pipeline_input.json` e exportando `context/output/pipeline_output.json` para encadeamento em Macro-Pipelines.

## 2. Arquitetura do Grafo (DAG)
O fluxo de execucao obedece a ordem topologica:
- **node-01-rea-web-saas**: Execucao da etapa aidd-rea-web-saas (Skill: `aidd-rea-web-saas`)
- **node-02-orchestrate-pipeline-creator**: Execucao da etapa aidd-orchestrate-pipeline-creator (Skill: `aidd-orchestrate-pipeline-creator`)

## 3. Como Executar

### Execucao Padrao
```bash
python run_pipeline.py
```

### Forcar Reexecucao Completa
```bash
python run_pipeline.py --force
```

## 4. Contratos de Entrada e Saida (Lego de Pipelines)
- Entrada Raiz: `context/input/pipeline_input.json`
- Saida Raiz: `context/output/pipeline_output.json`
- Handoffs Intermediarios: `context/handoffs/`
