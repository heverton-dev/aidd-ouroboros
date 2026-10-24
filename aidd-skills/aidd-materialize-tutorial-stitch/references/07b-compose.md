# 07b — Composição por spec (T5–T7 sem HTML à mão)

O agente escreve **um** arquivo por tutorial: `<tutorial>/spec.json`. O resto é script:

```bash
python HOME/scripts/tutorial.py produzir <tutorial>              # prepare → tts → retime → narration → compose
                                                                 # → audits → render → burn → audit final → idiomas → estado
python HOME/scripts/tutorial.py produzir <tutorial> --ate compose   # para conferir quadros antes do render (P5)
python HOME/scripts/tutorial.py produzir <tutorial> --de compose    # depois de mexer só nas ações
```

`compose` sozinho gera `composition/index.html` (câmera, rolagem, cursor, cliques, destaques, digitação, troca de tela,
abertura e fecho na marca do produto), grava `screen_box`/`focus_boxes` no storyboard (a legenda foge deles),
`target_box` no step-map, `composition/compose.json` (para o `audit composition`) e roda `sync-composition`.
Mesma spec + mesma voz = mesmo arquivo, byte a byte.

## 1. spec.json

```json
{
 "titulo": "Exportar o pipeline em CSV e PDF", "perfil": "Consultor", "rota": "/consultor",
 "auth": "produto do usuário; atalho de teste; só observação", "publico": "consultores",
 "title_card": ["Exporte o", "seu pipeline", "CSV ou PDF, com cuidado (LGPD)"],
 "outro_sub": "Agora você sabe exportar o seu pipeline.",
 "imgs": {"home": "home.png", "csv": "home-csv.png"}, "first_img": "home",
 "caixas": {"csv": [1500, 92, 96, 54]},
 "steps": [{"id": "s01", "title": "Exportar CSV", "user_action": "clicar em CSV", "result": "baixa a lista",
            "screen": "/consultor", "img": "csv", "img_before": "home", "box": "csv", "ui_text": ["CSV"]}],
 "scenes": [
  {"id": "c01", "layout": "title", "title": "Abertura", "steps": [], "narration": "Neste tutorial, você exporta o pipeline | em CSV ou em PDF.",
   "visual": "título", "camera": "fixa", "on_screen_text": ["Exporte o seu pipeline"], "actions": []},
  {"id": "c02", "layout": "zoom-focus", "title": "CSV", "steps": ["s01"], "narration": "Clique em CSV para baixar a lista | e abrir numa planilha.",
   "visual": "zoom no CSV", "camera": "zoom 1,4×", "on_screen_text": ["CSV"],
   "actions": [[0, "chip", "1", "Exportar CSV"], [0, "focus", "csv", 1.4, 0.7], [0.3, "cursor", "csv", 0.6],
               ["w:CSV", "click", "csv"], ["w:CSV+0.15", "show", "csv"], ["w:baixar", "callout", "Arquivo CSV gerado", "csv", "below", 2]]},
  {"id": "c03", "layout": "outro", "title": "Fecho", "steps": [], "narration": "Pronto. Agora você sabe exportar o seu pipeline.",
   "visual": "check", "camera": "fixa", "on_screen_text": ["Pronto!"], "actions": []}
 ]
}
```

- **Primeira cena `title`, última `outro`**; as do meio usam o palco (janela do app) e o `layout` descreve a intenção.
- `url` e `marca` vêm do `catalogo.json` (`produto.url`, `produto.marca`); a marca (`brand.css`, `logo.png`) de
  `<produto>/02-marca/brand/`. Fora de catálogo, ponha `"url"` e `"marca"` na spec.
- **Caixas** (`[x, y, w, h]` em pixels da captura): nome de `evidence/boxes.json` (`"home:busca"`, medido pelo
  `tutorial.py capture`), nome declarado em `caixas`, ou a lista direto. Erro de nome sugere o parecido.
- Narração com `|` = quebra de legenda (a voz não lê). Escreva para caber: ~2,5 palavras/s.

## 2. Ações: `[quando, verbo, ...]`

`quando`: segundos desde o início da cena, `"w:Palavra"` (o instante em que a voz diz a palavra; `#2` = 2ª
ocorrência; `+0.2`/`-0.1` desloca) ou `"end-0.5"`. **Cliques sempre em `w:`** — o `audit composition` avisa se não.

| Verbo | Argumentos | Efeito |
|---|---|---|
| `chip` | `"1", "Texto do passo"` | etiqueta numerada no topo (aparece na 1ª vez, pulsa nas seguintes) |
| `focus` | `caixa \| "center", escala, duração` | câmera aproxima/afasta no alvo (1.0 = tela inteira) |
| `scroll` | `y, duração` | rola a captura de página inteira até `y` (px da captura) |
| `cursor` | `caixa, duração` | cursor desliza até o centro da caixa |
| `click` | `caixa` | anel de clique + som; congela a câmera para o `target_box` do passo |
| `show` | `chave de imgs` | troca a tela (crossfade para frente, corte para trás) |
| `type` | `id, caixa, "texto", letras/s, recuo_x` | digita no campo simulado por cima da captura |
| `hide` | `id` | some com o campo simulado |
| `spot` | `caixa, duração` | moldura de destaque no elemento |
| `callout` | `"texto", caixa, "below\|above\|left\|right", duração` | balão na cor da marca, ao lado do alvo (nunca em cima: audit) |
| `badge` | `"texto", "ícone", caixa, lado, duração` | selo branco com ícone |

Verbo visual diferente em cenas seguidas (zoom → destaque → digitação → troca de tela) evita vídeo monótono.

## 3. Quando o template não basta

`composition/overrides/<cena>.js` entra no fim da timeline, com `tl`, `at(cena, t)`, `len(cena)` e `S` disponíveis;
`<cena>.html` entra nas sobreposições do palco. O `compose` nunca sobrescreve `overrides/`. Use para efeito único
(gráfico, 3D, transição especial) e só aí leia as skills HyperFrames (`07-build-render.md`).

## 4. Checagens que já rodam sozinhas

`audit composition` (cenas cobertas, `<audio>` com id, arquivos existem, sem `Date.now`/`Math.random`, `timeline.js`
em dia, destaque × clique, nada fora do quadro), `audit storyboard`, `audit captions` (legenda × foco),
`audit privacy` (e-mail, CPF/CNPJ, telefone, token; fictícios em `tutorial.config.json > privacidade.permitidos`)
e `audit final`. O agente olha só os quadros reduzidos (`tutorial.py frames <render> --out <pasta> --at 2,9,15`).
