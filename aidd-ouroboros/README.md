# AIDD-OUROBOROS — O Meta-Pipeline do Ciclo Infinito

Sistema de auto-geracao, engenharia reversa e materializacao continua de ativos digitais.
Autor: Heverton Eduardo Peres
Padrao: AIDD Universal Architecture (v1.0.0)

## 1. A Tese do Ciclo Infinito
O AIDD-OUROBOROS implementa computacionalmente a formulacao universal de sistemas com loops fechados de retroalimentacao:

Entrada Polimorfica -> Dissecacao REA -> Fabrica de Skills -> Orquestracao de Pipelines -> Materializacao -> Retroalimentacao

O ciclo e modelado na forma do oito deitado (infinito), composto por dois lobulos complementares:
- Lobulo Esquerdo (Desconstrucao do Mundo Real): Adquire videos, repositorios ou documentos tecnicos e os disseca em materia (conteudo tecnico) e forma (estrutura narrativa) com custo zero de alucinacao.
- Ponto de Fusao Central (Governanca e Contratos): Padroniza todas as comunicacoes atraves do schema canonico HANDOFF.json.
- Lobulo Direito (Materializacao e Construcao): Projeta grafos DAG no `aidd-orchestrate-pipeline-creator`, fabrica novas skills no `aidd-orchestrate-skill-creator` e entrega o produto final (software ou video MP4).

## 2. Como Operar (entrypoint soberano = raiz)

### Diagnostico (pre-voo global)
```bash
ouroboros --doctor
ouroboros --master-doctor
```

### Meta-fluxo NL -> Spec -> Pipeline (F1 + F2)
```bash
ouroboros --from-nl "criar pipeline X a partir de https://y"
# entrevista (agente) preenche SPEC_PIPELINE.json e marca approved=true
ouroboros --orchestrate ./SPEC_PIPELINE.json --output-dir ./ouroboros-out
```

### Ingestao de video de referencia (REA)
```bash
python aidd-ouroboros/run_ouroboros.py --video "https://www.youtube.com/watch?v=..."
```

## 3. Estrutura de Diretorios
- `OUROBOROS.json`: Grafo mestre de alta ordem com a definicao dos estagios globais.
- `run_ouroboros.py`: Delegador legado para o entrypoint da raiz (doctor/audit/video/NL).
- `schemas/`: Contratos formais em JSON Schema para validacao de payloads.
- `references/`: Fundamentacao teorica, arquitetura IPO e loops de feedback.
- `context/`: Diretorios de entrada, handoffs intermediarios e saida final.

## 4. Invariantes do Ecossistema
1. Todo componente gerado deve conter licenca MIT atribuida a Heverton Eduardo Peres (2026).
2. O frontmatter YAML de qualquer skill do ecossistema DEVE ter no maximo 25 palavras na description.
3. Comunicacoes, codigo e documentacao DEVEM manter estilo tecnico formal rigorosamente sem emojis.
4. Cobertura de testes unitarios obrigatoria com aprovacao nos Gates Enterprise antes de qualquer commit.
