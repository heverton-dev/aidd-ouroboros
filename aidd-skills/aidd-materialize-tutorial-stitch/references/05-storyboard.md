# 05 — Storyboard e quadros-chave (T5)

Objetivo: transformar roteiro + durações + evidências num plano de cenas **verificável por máquina** (`storyboard.json`) e em quadros-chave estáticos aprovados antes de qualquer animação.

## 1. Menu de layouts de tutorial

O agente escolhe o layout de cada cena a partir deste menu, variando para não repetir o mesmo layout mais de 2 vezes seguidas.

| Layout | Uso | Composição |
|---|---|---|
| `title` | gancho e abertura | título grande + subtítulo + mundo do estilo; logo pequeno |
| `app-full` | contexto, "onde estamos" | screenshot do passo na `AppWindow` ocupando ~80 % do quadro |
| `zoom-focus` | a ação principal de um passo | punch-in no `target_box` (1,6× a 2,5×), resto desfocado/escurecido, cursor clica |
| `callout` | explicar um elemento | `AppWindow` + `Callout` ancorado no elemento + seta curta |
| `cursor-path` | sequência de 2 a 3 cliques próximos | cursor percorre curvas entre alvos, anel em cada clique, stills trocam no clique |
| `split` | comparar antes/depois ou listar opções | metade texto/lista, metade tela |
| `step-list` | visão geral do fluxo | lista numerada dos passos com o atual destacado |
| `device-frame` | mobile em 16:9 | aparelho centralizado com a tela do passo + texto ao lado |
| `pip` | gravação do apresentador (se houver) | apresentador em círculo/canto, tela do app no resto |
| `result` | estado final | tela final com destaque no resultado + check animado |
| `outro` | fecho / CTA | logo, frase, URL ou próximo tutorial |

## 2. Quadros-chave (stills A → N)

Inspirado na técnica A→B→C→D: cada cena tem um **quadro de entrada** e um **quadro de saída**; a cena seguinte começa exatamente no quadro de saída da anterior (ou numa transição explícita). Isso garante continuidade.
- Para tutoriais, os quadros são composições dos **screenshots reais** com o layout aplicado (moldura, zoom, callout, texto).
- Gere os stills como HTML estático da cena no instante de entrada e de saída e fotografe com `npx hyperframes snapshot --at <t>` depois do esboço da composição, ou desenhe-os como wireframe descritivo quando a composição ainda não existir.
- Texto na tela entra **primeiro nos stills**: corrigir typo num still é barato.
- Nunca "edite" um still aprovado: gere um novo e mantenha o anterior intacto até a aprovação.

## 3. Formato `storyboard.json`

Esquema completo em `templates/storyboard.json`. Validado por `tutorial.py audit storyboard`.

```json
{
  "meta": {
    "title": "Gerar seu primeiro relatório",
    "width": 1920, "height": 1080, "fps": 30,
    "duration": 42.0,
    "language": "pt-BR",
    "style": "clean-product",
    "voice": "pf_dora",
    "wps": 2.5,
    "screen_box": [320, 150, 1280, 720]
  },
  "scenes": [
    {
      "id": "c03",
      "start": 9.2, "end": 15.0,
      "layout": "zoom-focus",
      "steps": ["s03"],
      "narration": "Clique em “Período” e escolha “Últimos 30 dias”. A tabela se atualiza na hora.",
      "audio": "audio/c03.wav",
      "visual": "Push-in no botão Período; cursor entra pela direita em curva, clica (anel); menu abre; segundo clique em Últimos 30 dias; corte para a tabela recarregada com shimmer.",
      "camera": "drift 3 % para dentro; zoom 1,8× no target_box s03",
      "on_screen_text": ["Período → Últimos 30 dias"],
      "keyframe_in": "keyframes/c03-in.png",
      "keyframe_out": "keyframes/c03-out.png",
      "transition_out": "zoom-through no resultado",
      "redact": ["coluna Cliente"],
      "zoom": 1.8,
      "focus_boxes": [[880, 250, 420, 90]]
    }
  ]
}
```

Regras que o `audit storyboard` verifica:
- primeira cena começa em 0; cenas contíguas (fim de uma = início da próxima, tolerância 0,05 s); última termina em `meta.duration`;
- cada passo do `step-map.json` aparece em **exatamente uma** cena (exceto passos marcados `"excluded": true`);
- todo passo referenciado tem arquivo de evidência existente;
- narração cabe na cena: `palavras ≤ duração × wps × 1,1`;
- cada item de `on_screen_text` tem no máximo 7 palavras; no máximo 3 itens por cena;
- `layout` pertence ao menu; o mesmo layout não aparece mais de 2 vezes seguidas;
- cena com duração mínima de 1,5 s.

### Geometria do foco (posição da legenda)

A legenda é posicionada por cálculo, não por olho (`09-acabamento.md` §2). Para isso o storyboard diz onde a tela e o foco aparecem no quadro:
- `meta.screen_box` (ou `screen_box` na cena, se mudar): `[x, y, w, h]` em pixels do quadro onde o screenshot capturado é exibido sem zoom (ex.: captura 1920×1080 a 2/3 numa `AppWindow` em 320,150 → `[320, 150, 1280, 720]`). Sem ele, vale o screenshot encaixado no quadro inteiro.
- `zoom` da cena (número) ou o "1,8×" escrito em `camera`: o punch-in é em torno do centro do `target_box` (transform-origin no alvo), como o `FocusZoom` faz.
- `focus_boxes`: `[[x, y, w, h], …]` em pixels do quadro para **tudo que a composição desenha por cima** e não pode ficar sob a legenda (callout, chip de passo, selo, cartão de título). O que não for declarado aqui o audit não enxerga.
- `focus_boxes_9x16` (e `_1x1`, `_4x5`): o mesmo para a composição nativa daquele formato.
- `caption_position` (`base`/`topo`/`meio`): fixa a posição da legenda numa cena.

Depois do `tts`, rode `tutorial.py audit captions <projeto>` junto com o `audit storyboard`.

## 4. Lista do que falta

Ao fim do storyboard, liste para o usuário o que o agente **não** tem: logo em SVG, trilha sonora, dados fictícios para preencher formulário, screenshot de um passo `unknown`.

Gate **P4**: `audit storyboard` sem erros + o usuário aprova a tabela de cenas (id, tempo, layout, narração, visual) e os quadros-chave.
