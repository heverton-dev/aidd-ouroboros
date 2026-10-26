# Manual de Instrucoes: google-flow-story-video

Pipeline autonomo composivel e deterministico criado pelo aidd-pipeline-creator.

## 1. Visao Geral
Este pipeline automatiza a cadeia de execucao completa para google-flow-story-video.
Opera como uma **peca de Lego composivel**, consumindo `context/input/pipeline_input.json` e exportando `context/output/pipeline_output.json` para encadeamento em Macro-Pipelines.

## 2. Arquitetura do Grafo (DAG)
O fluxo de execucao obedece a ordem topologica:
- **node-01-craft-story-ptbr**: Execucao da etapa aidd-craft-story-ptbr (Skill: `aidd-craft-story-ptbr`)
- **node-02-motion-remotion-core**: Execucao da etapa aidd-motion-remotion-core (Skill: `aidd-motion-remotion-core`)
- **node-03-materialize-video-synth**: Execucao da etapa aidd-materialize-video-synth (Skill: `aidd-materialize-video-synth`)

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
