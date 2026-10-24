# RULES.md - Gates e Circuit Breakers (Canal Dark Avatar)

## Gate 1: Presenca do Handoff de Entrada
- O pipeline exige `context/input/upstream_handoff.json` valido antes de iniciar a execucao.

## Gate 2: Sincronia de Audio e Video
- A faixa de voz neural DEVE possuir duracao compativel com o clipe renderizado pelo Remotion.

## Gate 3: Resolucao Padrao
- Todos os renders gerados DEVEM seguir a resolucao minima de 1920x1080 com framerate de 60 ou 30 fps.
