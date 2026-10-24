# 07 — Build, cena piloto e render (T6 e T7)

> **Com `spec.json`, este arquivo não é lido:** `tutorial.py compose`/`produzir` faz T6–T8 (`07b-compose.md`).
> Ele vale para composição escrita à mão (rotas sem DOM, estilos 3D) e para `composition/overrides/`.

## Rota padrão: HyperFrames

Se a harness tem a skill `hyperframes` (e `hyperframes-core`, `hyperframes-animation`, `hyperframes-cli`) instalada, **leia-as no momento do build** e siga o contrato delas (atributos `data-*`, `class="clip"`, sub-composições, determinismo). Elas prevalecem sobre este resumo em qualquer detalhe técnico.

1. **Projeto**: dentro de `tutorials/<slug>/composition/`:
   ```bash
   npx hyperframes init . --non-interactive --resolution landscape   # portrait | square conforme o brief
   ```
   Copie as evidências usadas para `composition/assets/` (caminhos relativos na composição).
2. **Componentes compartilhados primeiro** (do `blueprint.md`): `AppWindow`, `Cursor`, `FocusZoom`, `Callout`, `StepChip`, `TitleCard`, `OutroCard`, `Redact`. Uma sub-composição ou snippet reutilizável cada. Antes de construir à mão um efeito nomeado (glitch, shimmer, grão, terminal, gráfico), procure no registro: `npx hyperframes catalog` / skill `hyperframes-registry`.
3. **Uma cena por sub-composição**, com o id do storyboard (`data-composition-id="c03"`), início e duração exatos do `storyboard.json`; o áudio da narração da cena entra na faixa de áudio no mesmo início.
   **Tempos nunca fixos no código.** Marque cada elemento temporizado com `data-scene="c03"` (ou um intervalo `data-scene="c01-c03"`, ou `data-scene="all"`) e efeitos pontuais com `data-scene="c02" data-offset="0.8"`; rode
   ```bash
   python HOME/scripts/tutorial.py sync-composition tutorials/<slug>
   ```
   que grava `composition/timeline.js` (`window.TL.scenes.<id>.start/end` e `window.TL.words`) e reescreve `data-start`/`data-duration`. No JS, anime com `at("c03", 0.65)` = início da cena + 0,65 s. Assim um novo TTS ou `retime` não quebra a sincronia: basta rodar `sync-composition` de novo.
   **Sincronia com a fala:** posicione o clique do cursor no instante em que a narração diz o rótulo (de `audio/<cena>.words.json`), não "mais ou menos" na cena. Isso exige que a janela já esteja no lugar no início da cena: faça a entrada da janela no fim da cena anterior (continuidade A→B).
4. **Cena piloto** (gate P5): construa só a cena mais representativa (normalmente o primeiro `zoom-focus`) com todos os componentes, rode
   ```bash
   npx hyperframes check --json
   npx hyperframes snapshot --composition c03 --frames 5 -o ../snapshots/pilot
   ```
   e mostre os stills ao usuário. Seja exigente: cor, layout, velocidade, alinhamento, tamanho do texto. **Ajuste o piloto até ser aprovado; só então construa o resto.** Lições do piloto vão para `rules.md`.
5. **Build do lote** (T7): demais cenas seguindo o plano travado. Cenas independentes podem ir para subagentes, cada um com o prompt mestre, os componentes prontos e só a sua cena.
6. **Checagem do lote**:
   ```bash
   npx hyperframes check --json --at-transitions
   npx hyperframes snapshot --review -o ../snapshots/review
   ```
7. **Render**:
   ```bash
   python HOME/scripts/tutorial.py render tutorials/<slug>      # → renders/<slug>.raw.mp4 (sem legenda)
   ```
   Envolve `npx hyperframes render --quality delivery --video-frame-format png` com **TEMP/TMP locais** (`renders/.tmp`) e até 3 tentativas reduzindo workers. Motivo: no Windows, os frames e o áudio intermediários em `%TEMP%\hf-render-*` sumiram no meio do render em 5 execuções seguidas; com TEMP local passou em todas. A legenda é queimada depois (`09-acabamento.md`). Overlay transparente para editor externo: `npx hyperframes render --format mov` (ProRes 4444 com alfa) ou `--format webm`.

Armadilhas observadas no teste de validação (HyperFrames 0.8.185, Windows):
- O **frame 0 é a miniatura** em players sociais: o título ou a imagem-chave já devem estar visíveis em `t = 0` (o `check` avisa com `first_frame_empty`).
- Dois tweens no mesmo elemento e propriedade não podem se sobrepor no tempo (`overlapping_gsap_tweens`): encadeie-os.
- Zoom sem deslocar o alvo: use `transformOrigin` igual ao centro do `target_box` **relativo à janela**; o ponto clicado fica parado na tela enquanto o resto cresce, e o cursor não precisa ser recalculado.
- Render com `ENOENT ... hf-render-*` ou `audioPadTrim: failed to probe audio`: são arquivos temporários apagados durante o render. Use `tutorial.py render` (TEMP local); manualmente, defina `TEMP`/`TMP` para uma pasta do projeto antes de `npx hyperframes render`.
- Barra de URL e outros textos de "cromo" da janela são textura, não leitura: marque com `data-layout-ignore data-layout-allow-occlusion` para o `check` não reprovar quando o chip de passo os cobre durante o zoom.
- Texto de leitura (chips, callouts, rótulos) com no mínimo 28 px a 1080p; a última linha do filme fica ≥ 2 s na tela.

## Rota 3D premium: Three.js dentro da composição

Para os estilos `glass-3d` e `clay-soft`, use o adaptador Three.js da skill `hyperframes-animation` dentro da composição HyperFrames (a cena 3D é dirigida pelo mesmo `t`). Princípios do prompt mestre, bloco 2 e 7:
- Screenshots do app viram **textura de canvas** em painéis (`RoundedBoxGeometry` ou plano com cantos arredondados), redesenhada por frame se houver cursor/realce dentro dela.
- Câmera em perspectiva com keyframes de posição e `lookAt`; cenas em posições 3D distintas; deriva dentro, whip entre.
- Shaders: domo de fundo com gradiente GLSL, dissolve por ruído com borda brilhante para materializar/desmaterializar elementos, fresnel para vidro.
- Pós-processamento: HDR half-float + MSAA 4×, `UnrealBloomPass` com threshold alto, tone mapping neutro/ACES, passe final de grão + vinheta + aberração leve; clamp antes de `pow()`.
- Mantenha a UI **legível**: o 3D é moldura e transição, não pode distorcer o texto da interface no momento em que ele é explicado (painel de frente para a câmera durante a ação).

## Rota alternativa sem HyperFrames

Se `npx hyperframes` não estiver disponível e o usuário não autorizar instalá-lo: página HTML única com timeline GSAP pausada e função global `window.seek(t)`; script Playwright que abre a página no tamanho do vídeo, chama `seek(i / fps)` para cada frame e salva PNGs; `ffmpeg -framerate <fps> -i frame_%05d.png -i narration.wav -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest out.mp4`. É exatamente o processo "screenshot do navegador 60 vezes por segundo" da metodologia.

## Estilos: parâmetros de partida

| Estilo | Fundo | Janela | Movimento padrão |
|---|---|---|---|
| `clean-product` | gradiente radial claro do acento a 6 % sobre `#F7F8FA` | raio 14 px, sombra `0 30px 80px rgba(0,0,0,.18)` | entrada com `rotationX: 8 → 0`, `y: 40 → 0`, 0,7 s `expo.out` |
| `glass-3d` | domo escuro com 4 blobs (violeta, laranja, azul, rosa) | vidro fosco, transmission 1, roughness 0,4 | câmera voa entre painéis, whip `expo.inOut` 0,5 s |
| `clay-soft` | estúdio off-white, piso com grade de pontos | painel clay pastel, borda com rim light | dissolve com borda índigo, órbita 6° |
| `paper-editorial` | papel off-white com grade de pontos | recorte com sombra dura curta | elementos caem e giram 3 a 6°, marker sweep |
| `dark-tech` | navy `#01040B` com campo de pontos | borda 1 px ciano a 30 % | scan line, digitação de terminal, glow ciano |

## Paralelismo e tempo

Render e build demoram. Rode em segundo plano quando a harness permitir e avise o usuário para voltar quando terminar. Variações (vertical, curta) podem ser geradas em paralelo em pastas/worktrees separadas.
