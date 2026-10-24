# AIDD-OUROBOROS — O Meta-Pipeline do Ciclo Infinito

Sistema de auto-geracao, engenharia reversa e materializacao continua de ativos digitais.
Autor: Heverton Eduardo Peres
Padrao: AIDD Universal Architecture (v1.0.0)

## 1. A Tese do Ciclo Infinito
O AIDD-OUROBOROS implementa computacionalmente a formulacao universal de sistemas com loops fechados de retroalimentacao:

Entrada Polimorfica -> Dissecacao REA -> Fabrica de Skills -> Orquestracao Swarm -> Materializacao -> Retroalimentacao

O ciclo e modelado na forma do oito deitado (infinito), composto por dois lobulos complementares:
- Lobulo Esquerdo (Desconstrucao do Mundo Real): Adquire videos, repositorios ou documentos tecnicos e os disseca em materia (conteudo tecnico) e forma (estrutura narrativa) com custo zero de alucinacao.
- Ponto de Fusao Central (Governanca e Contratos): Padroniza todas as comunicacoes atraves do schema canonico HANDOFF.json.
- Lobulo Direito (Materializacao e Construcao): Projeta grafos DAG no aidd-skill-swarm, fabrica novas skills no aidd-skill-creator e entrega o produto final (software ou video MP4).

## 2. Como Operar o Meta-Pipeline

### Diagnostico de Ambiente (Pre-voo Global)
```bash
python run_ouroboros.py --doctor
```

### Ingestao de Video de Referencia (Engenharia Reversa)
```bash
python run_ouroboros.py --video "https://www.youtube.com/watch?v=..."
```

### Ingestao de Repositorio do GitHub (Scout & Refactor)
```bash
python run_ouroboros.py --github-scout "termo de busca"
```

### Execucao Continua a partir de Especificacao Socratica
```bash
python run_ouroboros.py --socratic "Descricao da ideia"
```

## 3. Estrutura de Diretorios
- `OUROBOROS.json`: Grafo mestre de alta ordem com a definicao dos estagios globais.
- `run_ouroboros.py`: Runner deterministico com tolerancia a falhas e telemetria.
- `state.json`: Registro de estado e checkpoints dos ciclos executados.
- `schemas/`: Contratos formais em JSON Schema para validacao de payloads.
- `references/`: Fundamentacao teorica, arquitetura IPO e loops de feedback.
- `context/`: Diretorios de entrada, handoffs intermediarios e saida final.

## 4. Invariantes do Ecossistema
1. Todo componente gerado deve conter licenca MIT atribuida a Heverton Eduardo Peres (2026).
2. O frontmatter YAML de qualquer skill do ecossistema DEVE ter no maximo 25 palavras na description.
3. Comunicacoes, codigo e documentacao DEVEM manter estilo tecnico formal rigorosamente sem emojis.
4. Cobertura de testes unitarios obrigatoria com aprovacao nos 4 Gates Enterprise antes de qualquer commit.
