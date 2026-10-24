# 12 — Saídas: formatos, resoluções, canais e legibilidade

Um tutorial tem **um render-mestre** (a composição, em 1080p no formato principal) e **quantas saídas o usuário quiser**: qualquer combinação de formato (16:9, 9:16, 1:1, 4:5) e resolução (480p, 720p, 1080p), cada uma com sua legenda queimada no tamanho final. Tudo fica registrado em `tutorial.config.json` (`saidas`, `canais`) e em `ESTADO.md` (Registro de decisões).

## 1. Definir as saídas

- **Por canal** (preferível; o usuário diz onde o vídeo será usado):
  `--canal instagram-reels,plataforma-ensino`

| Canal | Saídas | Legenda | Zonas seguras (topo/base) | Loudness | Limite |
|---|---|---|---|---|---|
| `instagram-reels` | 9:16 1080p | bold-pop g | 14 % / 22 % | -14 LUFS | 90 s |
| `instagram-feed` | 4:5 1080p | highlight | 5 % / 10 % | -14 | 60 s |
| `tiktok` | 9:16 1080p | bold-pop g | 12 % / 25 % | -14 | 180 s |
| `youtube-shorts` | 9:16 1080p | bold-pop g | 10 % / 20 % | -14 | 180 s |
| `youtube` | 16:9 1080p | highlight | 0 / 8 % | -14 | — |
| `plataforma-ensino` | 16:9 1080p + 720p | boxed | 0 / 10 % | -16 | — |
| `central-de-ajuda` | 16:9 1080p + 720p | clean | 0 / 8 % | -16 | — |
| `linkedin` | 1:1 1080p | highlight | 0 / 10 % | -14 | 600 s |
| `whatsapp` | 9:16 720p (até 2 Mbit/s) | bold-pop g | 0 / 12 % | -14 | 180 s |
| `apresentacao` | 16:9 1080p | sem legenda queimada (`.srt`) | 0 / 8 % | -16 | — |

- **Por formato e resolução**: `--formatos 16:9,9:16 --resolucoes 720p,1080p` (produto cartesiano).
- No `init`/`config`, as flags definem as saídas desejadas; o formato da **primeira** saída vira o formato do mestre (composição nativa nele).

## 2. Gerar e adequar

```bash
python HOME/scripts/tutorial.py render tutorials/<slug>                     # mestre: renders/<slug>.raw.mp4
python HOME/scripts/tutorial.py burn tutorials/<slug>                       # principal: renders/<slug>.mp4 (+ .srt)
python HOME/scripts/tutorial.py export tutorials/<slug>                     # todas as saídas registradas
python HOME/scripts/tutorial.py export tutorials/<slug> --formatos 9:16,1:1 # adequar: acrescenta e gera
python HOME/scripts/tutorial.py export tutorials/<slug> --resolucoes 720p,480p
python HOME/scripts/tutorial.py export tutorials/<slug> --canal instagram-reels
python HOME/scripts/tutorial.py export tutorials/<slug> --legenda boxed     # mudar o tipo de legenda destas saídas
```
Arquivos: `renders/<slug>-<formato>-<resolução>.mp4` (ex.: `acessar-o-sistema-9x16-1080p.mp4`) + `.srt` + `.ass`.

Modos de adequação (`--modo`, padrão `auto`):
| Modo | Quando | Como | Qualidade |
|---|---|---|---|
| `escalar` | mesma proporção do mestre | redimensiona com Lanczos (+ nitidez leve ao reduzir) | ótima até 720p; 480p no limite |
| `reenquadrar` | outra proporção, rápido | recorta a **zona central de conteúdo** do mestre (2/3 da largura em 16:9) e encaixa no novo quadro sobre o próprio vídeo desfocado, respeitando as zonas seguras do canal | boa em 1:1 e 4:5; em 9:16 a interface fica menor |
| `nativo` | outra proporção, melhor resultado | o agente recompõe as cenas em `composition-<formato>/` (mesmo storyboard, áudio e marca; layouts e zooms pensados para o quadro), `tutorial.py render --composicao composition-9x16 --formato 9:16`; o `export` passa a usar esse mestre | a melhor; recomendada para Reels/Shorts/TikTok |

### 2.1 Captura responsiva (flag `--responsivo`)

Se o produto é responsivo, a saída 9:16 (ou 1:1, 4:5) deve nascer da **tela real naquele tamanho**, não de um recorte do desktop.
```bash
python HOME/scripts/tutorial.py responsive <url> --out <pasta> --formatos 9:16,1:1 --caminhos "/,/rota" --projeto <projeto>
python HOME/scripts/tutorial.py responsive <url> --out <pasta> --formatos 9:16 --atalho "Consultor"     # área logada
```
O medidor (`scripts/responsive.mjs`, Playwright do REA + Chrome local, só leitura) abre cada página no viewport do formato e mede: `meta viewport`, rolagem horizontal da página, elementos vazando da tela (fora de carrosséis e tabelas com rolagem própria), conteúdo cortado dentro desses contêineres, menor texto e fração de textos < 10 px. Veredito por página e por formato: **sim**, **parcial** (rolagem interna cortando muito conteúdo, ex.: tabela larga) ou **não**. Os critérios foram calibrados olhando screenshots reais.

| `--responsivo` | Captura para 9:16/1:1/4:5 |
|---|---|
| `auto` (padrão) | usa o veredito do `responsive`: `sim`/`parcial` → nativa; `nao` → reenquadra o desktop |
| `sim` | sempre nativa |
| `nao` | sempre reenquadra |

Viewports de captura nativa: 9:16 → 390×844 @3 (imagens 1170×2532, emulação móvel); 1:1 → 820×820 @2; 4:5 → 768×960 @2. Capture com o REA (`capture_browser_scenario` com `environment.viewport`) e componha em `composition-<formato>/`:
- a tela ocupa a **largura inteira** do quadro e a câmera **desce** até cada elemento (foco abaixo da faixa de cabeçalho e acima da faixa de legenda do canal);
- o chip de passo mora numa **faixa de cabeçalho** própria (a tela cobre o quadro todo; chip solto cobriria a UI);
- etiquetas e selos ao lado/abaixo do elemento, nunca sobre links vizinhos.
No laboratório, a mesma tela ficou com o menor texto em ~28 px no 9:16 nativo contra ~20 px no reenquadrado.

**Regra de composição para reenquadrar bem:** mantenha o conteúdo importante (janela, cursor, callouts, chips, **selos**) na **zona central de 1280 px** do mestre 16:9 (x de 320 a 1600). Legendas são queimadas depois, por saída. (No laboratório, um selo posto à direita do botão, até x ≈ 1780, saiu cortado no 9:16 reenquadrado.)

## 3. Qualidade e legibilidade

- Codificação por resolução: H.264 High, `yuv420p`, CRF 18 (1080p), 19 (720p), 20 (480p), preset `slow`, `+faststart`, AAC 160 kbit/s (128 em 480p), loudness normalizado ao canal (`loudnorm`), teto de bitrate quando o canal exige (WhatsApp).
- Legendas queimadas **no tamanho final** de cada saída (escala com a resolução), fora das zonas seguras do canal (base **e** topo) e com posição automática no quadro daquela saída: o foco do mestre é levado pelo mesmo recorte/escala do export. No modo `nativo`, o foco vem de `focus_boxes_<formato>` das cenas (sem elas, o audit avisa que não verificou).
- Contraste da legenda: se a cor de acento for escura, a palavra ativa fica branca com contorno grosso na cor da marca.
- **Checagem de legibilidade** em cada export: estima o tamanho do menor texto de leitura da interface na saída (`texto_minimo_px` do mestre × escala; padrão 24 px) e classifica: **≥ 14 px legível**, **10–14 px no limite**, **< 10 px ilegível** (calibrado olhando frames reais). O resultado vai para o terminal e para o `ESTADO.md`. Ilegível → recomende resolução maior ou modo `nativo`.
- Duração acima do limite do canal gera aviso registrado.
- `audit final` confere cada saída registrada (existe, dimensões corretas, `.srt` ao lado).
