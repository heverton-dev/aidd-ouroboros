# Manual de Instrucoes: Canal Dark Tech Brasil com Avatar e Remotion

Pipeline autonomo de engenharia reversa audiovisual, transcriacao cultural para PT-BR e materializacao de video 1080p60 para canais dark.

## 1. Visao Geral
Este pipeline processa videos tutoriais de tecnologia da gringa (ex: canal GenAI with Keera), extrai a estrutura narrativa e o conteudo tecnico, adapta as falas para portugues do Brasil com alta retencao (hook de 15 segundos), gera animacoes em codigo no Remotion e realiza a composicao final via FFmpeg.

## 2. Arquitetura do Grafo (DAG)
O pipeline e composto por 3 nos estritos em ordem topologica:
- `node-01-storycraft` (Skill: aidd-dark-storycraft): Transcria o roteiro para PT-BR e formata as cenas.
- `node-02-remotion-motion` (Skill: aidd-remotion-motion): Gera os parametros fisicos de animacao Remotion a 60 fps.
- `node-03-hybrid-stitch` (Skill: aidd-video-materializer): Sintetiza a voz neural em PT-BR, renderiza os graficos e entrega o MP4.

## 3. Como Executar

### Execucao Direta
```bash
python run_pipeline.py
```

### Forcar Reexecucao de Todas as Etapas
```bash
python run_pipeline.py --force
```

## 4. Estrutura de Diretorios
- `context/input/`: Handoff de entrada gerado pela engenharia reversa (`upstream_handoff.json`).
- `context/handoffs/`: Contratos intermediarios (`01_roteiro_ptbr.json`, `02_motion_assets.json`).
- `context/output/`: Video final gerado (`video_final_keera_br.mp4`) e faixas de audio.
- `skills/`: Micro-skills encapsuladas dedicadas ao canal dark.
- `references/`: Evidencias e documentos tecnicos de referencia.

## 5. Rastreamento e Estado
O arquivo `state.json` mantem o registro do progresso de cada no para recuperacao automatica em caso de interrupcao.
