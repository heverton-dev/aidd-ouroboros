# 00 — Metodologia de origem

Esta skill condensa nove vídeos de referência (transcritos localmente com Whisper e com os prompts lidos dos frames). A pesquisa completa fica no projeto de origem, em `research/metodologia.md`; este arquivo é autossuficiente.

| Fonte | Contribuição |
|---|---|
| Matt Penny, *Claude + Three.js = Premium 3D Motion Graphics* (`CCUSpJkAfgU`) | vídeo = site animado gravado; Three.js + shaders; render determinístico por `t`; prompt em 8 blocos; checar stills antes do render |
| kaye.creatives, *Claude Motion / Opus 5.5* (`AsvN_feasyY`) | prompt é 90% do trabalho; referências + ativos de marca + direção; iteração travada |
| *Video Editors… adopt Claude Code* (`Xwa5x0jJI0Y`) | HyperFrames; site → vídeo; agente escreve o próprio prompt pelo guia; passos pequenos |
| *Claude Code Just Automated My Video Production* (`uK-SNyzmFGI`) | screenshots reais; vídeo de referência → markdown de tokens e cenas; roteiro primeiro; componentes compartilhados; wireframe aprovado antes de construir |
| @theguneytopcu, *30s AI Motion Graphics* (`AO3bgthoqQU`) | voz primeiro (25 palavras/10 s); quadros-chave A→D; regras do projeto escritas uma vez; texto curto nos stills |
| @theguneytopcu, *FREE Caption Tool* (`51VvpgOLmgk`) | legendas locais com Whisper; 5 estilos; correção de palavra sem perder timing; `.srt` |
| @theguneytopcu, *Claude + DaVinci Resolve* (`Ewck-gckuzU`) | roteiro × transcrição × timeline; cada trecho exatamente uma vez; salvar o processo como skill |
| @theguneytopcu, *Automated Google Flow* (`JEla_mdlfxs`) | 4 perguntas antes; plano antes das imagens; continuidade pelo último frame; gate de custo |
| @theguneytopcu, *Claude Code + Remotion Edited this Entire Video* (`QYUV9FjR5-M`) | storyboard a partir de áudio + roteiro; menu de layouts; cena piloto com o modelo mais forte; overlay com alfa; falha vira regra |

## Os princípios, em uma tela

1. **Código, não modelo de vídeo.** HTML/CSS/JS renderizado frame a frame. Barato para iterar (uma alteração custa tokens, não uma nova geração paga).
2. **Determinismo.** Toda animação é função de `t`; nada de `Date.now()`, `requestAnimationFrame` livre ou aleatoriedade sem semente. Mesmo input → mesmo vídeo.
3. **Especificidade.** O quê acontece e **quando** (cena + timing). Quando o usuário está aberto, ofereça 3 ideias em texto e deixe escolher.
4. **Profundidade premium.** Câmera que se move entre cenas **e** elementos que se movem dentro da cena; shaders para glow, reflexo, grão, dissolve. Para tutoriais, profundidade sutil: o conteúdo (a UI real) é o protagonista.
5. **Referências mandam no estilo.** Extraia só as palavras de estilo (cor, luz, material, movimento), nunca a história.
6. **Voz primeiro, visual depois.** O áudio diz quando; o roteiro diz o quê.
7. **Stills antes de movimento; piloto antes do lote.**
8. **Componentes compartilhados antes das cenas.**
9. **Iteração travada.** Mude só o delta; o que funciona fica congelado.
10. **Verificação antes da entrega.** Sobreposição, texto pequeno, texto fora do quadro, contraste, sincronia, cobertura do roteiro.
11. **Toda falha vira regra** num arquivo lido em toda execução.
12. **O humano decide gosto.** O agente executa; o usuário aprova em gates curtos.

## Por que HyperFrames é o renderizador padrão

- Já instalado como CLI (`npx hyperframes`) com `capture` (site → componentes e tokens), `tts` local (Kokoro, inclui `pt-br`), `transcribe` (Whisper/Parakeet), `check` (lint + layout + contraste), `snapshot` (stills em tempos exatos) e `render` (MP4, WebM/MOV com alfa, GIF, PNG sequence).
- HTML puro (não React): segundo os autores, LLMs produzem saídas mais criativas e o mesmo código serve de camada de edição humana (Studio com timeline).
- Three.js, Lottie, Anime.js, CSS e WAAPI entram como adaptadores dentro da mesma composição, então a rota 3D premium não exige outro framework.
