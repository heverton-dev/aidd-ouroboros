# 09 — Acabamento: áudio, legendas e exportações (T8)

## 1. Áudio

- Efeitos: `python HOME/scripts/tutorial.py sfx tutorials/<slug>/composition/assets` gera `click.wav`, `pop.wav`, `whoosh.wav` e `tick.wav` localmente (ffmpeg, sem licença de terceiros). Clique no instante do anel do cursor, whoosh 0,35 s antes de cada troca grande de cena, pop quando surge um callout. Desligue com `--sfx off`.
- Todo `<audio>` precisa de `id`; sem ele o HyperFrames renderiza **mudo** (o `check` acusa `media_missing_id`).
- Narração sempre em volume cheio; trilha a **-18 a -22 dB** abaixo da voz, com ducking durante a fala (skill `hyperframes-audio` para fades, ducking e automação de volume).
- Efeitos sonoros discretos opcionais: clique no anel do cursor, whoosh nas transições de cena (curtos, -12 dB).
- Se a narração passar do fim visual, **segure o último frame** até a fala acabar; nunca corte a voz.
- Normalização: `npx hyperframes normalize-audio` para casar o volume da trilha com a voz; alvo de mixagem final perto de -14 LUFS (YouTube).

## 2. Legendas (queimadas + `.srt`) — obrigatórias salvo `--legenda nenhuma`

O render da composição sai **sem** legenda (`renders/<slug>.raw.mp4`); a legenda é queimada depois, a partir dos tempos por palavra gravados pelo `tts`:
```bash
python HOME/scripts/tutorial.py render tutorials/<slug>      # → renders/<slug>.raw.mp4
python HOME/scripts/tutorial.py burn tutorials/<slug>        # → renders/<slug>.mp4 + .srt + .ass (estilo da flag --legenda)
python HOME/scripts/tutorial.py burn tutorials/<slug> --style bold-pop --out renders/variantes/<slug>-bold-pop.mp4   # variante
```
- Fonte dos tempos: `audio/<cena>.words.json` + início da cena no storyboard (exato com edge-tts; Whisper alinhado à grafia do roteiro nos demais motores). Sem esses arquivos, o `burn` transcreve o próprio render.
- Os blocos quebram no marcador `|` do roteiro, em pontuação, pausa > 0,6 s, limite de palavras e **nunca atravessam a troca de cena** (o `audit final` reprova se atravessarem).
- **Posição automática por bloco (padrão `--legenda-posicao auto`).** O `burn` e o `export` calculam, sem modelo, onde fica o foco de cada cena no quadro: o `target_box` de cada passo levado da captura para o vídeo pelo `screen_box` e ampliado pelo zoom da cena (`zoom` ou o "1,8×" do campo `camera`), mais as `focus_boxes` declaradas (callouts, chips, selos). Cada cena usa a primeira de **base → topo → meio** em que nenhum bloco cobre o foco (a legenda não pula dentro da cena). Se nenhuma serve para a cena inteira, cada bloco escolhe a sua; sem saída, fica a de menor sobreposição e o `audit captions` reprova. O registro de cada bloco (posição, retângulo, colisões) vai para `renders/<slug>.captions.json`.
- Posição fixa: `--legenda-posicao base|meio|topo` (no `burn`: `--position bottom|middle|top`) para o tutorial inteiro, ou `"caption_position": "topo"` numa cena do storyboard. Posição fixa nunca é mudada; só tem as colisões reprovadas pelo audit.
- Tamanho: `--legenda-tamanho p|m|g` (no `burn`: `--size`); `g` em vídeos verticais vistos no celular.
- **Gate:** `python HOME/scripts/tutorial.py audit captions tutorials/<slug>` (também roda dentro do `audit final`). Refaz a mesma decisão para o mestre e para cada saída do `tutorial.config.json`, no quadro e nas zonas seguras de cada uma. Roda sem render, logo depois do `tts`: use em T5 para corrigir o storyboard antes de animar.
- O `.srt` sai junto, já com a grafia do roteiro (para o YouTube e acessibilidade).
- Queimar de novo leva segundos: troque de estilo sem re-renderizar.
- Gravação do próprio usuário (sem `words.json`): `tutorial.py captions audio/narration.wav --lang pt` gera transcrição com tempos; corrija nomes de produto no `transcript.json` mantendo os tempos.

Estilos (flag `--legenda`; padrão `highlight` em 16:9 e `bold-pop` em 9:16; cor da palavra ativa pela flag `--acento`, padrão amarelo `#FFD43B`, que contrasta com qualquer fundo):
| Estilo | Visual |
|---|---|
| `highlight` | frase curta; a palavra falada ganha uma pílula na cor de acento (padrão 16:9) |
| `bold-pop` | 3 palavras grandes por vez; a palavra falada acende no acento e cresce 12 % (padrão 9:16) |
| `word-by-word` | cada palavra aparece no instante em que é dita |
| `clean` | legenda clássica, estática, 1 a 2 linhas |
| `boxed` | texto claro numa faixa escura translúcida (lê sobre qualquer fundo) |

Caixa: normal (padrão para tutorial), CAIXA ALTA (curtos), minúsculas (casual). Posição: automática por cena (seção acima); a regra do prompt mestre (bloco 3) é declarar em `focus_boxes` tudo que for desenhado por cima da tela.

Sempre entregue **também** o `.srt` separado (para o YouTube traduzir e para acessibilidade), mesmo quando a legenda está queimada.

## 3. Exportações

| Destino | Formato | Comando de partida |
|---|---|---|
| YouTube, docs, site | MP4 1920×1080 30 fps H.264 + `.srt` | `npx hyperframes render -o renders/<slug>.mp4 --quality delivery --video-frame-format png` |
| Shorts, Reels, TikTok | MP4 1080×1920, legenda queimada `bold-pop` | projeto em `--resolution portrait`, mesma rota |
| Feed quadrado | MP4 1080×1080 | `--resolution square` |
| Overlay para editor (DaVinci, Premiere) | MOV ProRes 4444 com alfa ou WebM com alfa | `--format mov` / `--format webm` |
| Prévia leve / docs | GIF curto (≤ 10 s) | `--format gif` |

Uma nova proporção **não** é só recortar: refaça T4 → T8 a partir do `step-map.json` e do `blueprint.md`, porque layout, tamanho de texto e zooms mudam.

## 4. Entregáveis

`renders/<slug>.mp4`, `renders/<slug>.srt`, `snapshots/review/`, `storyboard.json`, `script.md`, e um `ENTREGA.md` com: duração, formato, voz, estilo, lista de cenas, saída dos audits e o veredito.
