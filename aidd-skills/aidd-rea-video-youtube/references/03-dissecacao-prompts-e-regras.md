# 03 — Dissecação de Prompts e Engenharia de Instrução

## 1. A Anatomia em 8 Blocos do Prompt de Motion Design
Analisando criadores de ponta como Matt Penny, Viktor Kav e theguneytopcu, os prompts funcionais sempre obedecem a uma arquitetura modular rígida:

1. **Cabeçalho Técnico:** Duração total, framerate (60 fps), aspecto (16:9 ou 9:16), framework (Three.js, Remotion, Canvas) e o contrato determinístico de que todo movimento deriva do frame $f$ ou tempo $t$.
2. **Estilo & Atmosfera:** Vibe (clean tech, cyber dark, editorial paper), esquema de iluminação, materiais e um único tom de destaque cromático (*accent color*).
3. **Camada de Tipografia:** Famílias tipográficas separadas para display e código, tamanhos escalares relativos à tela e proteção de safe-zone contra cortes de UI.
4. **Cinemática & Câmera:** Movimento de lente (orbit, pan, dolly), velocidade de transição entre cenas (*expo ease* ou *spring whip*).
5. **Roteiro em Cenas Atômicas:** Lista estruturada de cada bloco de tempo com um verbo visual concreto ("desenha vetor", "expande card", "orbita nó").
6. **Fio Condutor Visual:** Um elemento contínuo que atravessa as transições de cena (ex: feixe de partículas, cabo de dados, trilha Bézier).
7. **Pós-processamento e Shaders:** Grain analógico, vinheta leve, bloom controlado para dar peso cinematográfico.
8. **Critérios de Validação:** Regra de ouro para o LLM conferir sobreposição de textos antes de entregar a composição.
