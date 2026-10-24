# 03 — Blueprint de estilo (T3)

Objetivo: decidir **uma vez** o sistema visual do tutorial, a partir do próprio alvo (marca) e, opcionalmente, de uma referência. Saída: `blueprint.md`. Toda cena posterior obedece a ele.

## 1. Tokens do alvo (sempre)

Extração determinística (preferida):
```bash
npx hyperframes capture <url-do-produto> -o <projeto>/capture --skip-vision --max-screenshots 4
python HOME/scripts/tutorial.py design-tokens <projeto>/capture --out <projeto>      # ou --out <catálogo>/compartilhado
```
Gera `design-tokens.json` (cores nomeadas pelas variáveis CSS do produto, paleta, fontes, raios, sombras, logo, com a origem) e `brand/brand.css` (as regras `@font-face` originais com `unicode-range`, apontando para os arquivos locais, e as variáveis `--brand-*`). Copie `brand/` para `composition/` e importe `brand/brand.css`; na composição use **só** `var(--brand-*)`, neutros e `rgba()` das cores da paleta. Verifique com `tutorial.py audit brand <projeto>`.

Para páginas com login, rode o `hyperframes capture` numa tela pública do mesmo produto (login, landing): o design system costuma ser o mesmo. Se não houver nenhuma, extraia do CSS observado pelo REA e registre a origem manualmente.

O que verificar (e completar à mão se faltar):
- **Cores**: fundo do app, superfície, texto primário, **um** acento da marca (hex). Se o app tem mais de um acento, escolha o da ação principal (botão primário).
- **Tipografia**: família da UI do app (para rótulos que imitam a interface) e família de títulos do vídeo (padrão: a mesma do app; se for genérica, use Inter / SF Pro / Geist).
- **Raio e sombra** dos cartões do app (para a moldura de janela e os callouts parecerem parte do produto).
- **Logo** (SVG se houver; senão PNG transparente) e **ícone** do produto.

## 2. Referência visual (opcional, V2)

De um vídeo/imagem de referência, registre só estilo:
| Campo | Exemplo |
|---|---|
| Paleta | `#0B0D12` fundo, `#F5F7FA` texto, `#6E56CF` acento |
| Tipografia | títulos geométricos pesados, rótulos mono |
| Ritmo | cena média 3,2 s; corte seco entre passos; respiro de 0,4 s no fim de cada ação |
| Câmera | push-in lento (2 a 4 %) durante a cena; whip/expo entre cenas |
| Transições | wipe com blur, zoom-through no elemento clicado |
| Texto | entra por palavra com leve subida (8 px) e opacidade |
| Efeitos | grão 3 %, vinheta leve, glow no acento |
| Layouts recorrentes | janela flutuante com sombra, split texto/tela |

Nunca copie a história, o texto ou a marca da referência.

## 3. Estilos nomeados (quando o usuário não traz referência)

| Estilo | Quando usar | Mundo | Movimento |
|---|---|---|---|
| `clean-product` (padrão) | SaaS, painéis, docs | fundo claro neutro com gradiente sutil do acento; janela do app flutuando com sombra suave | push-in suave, cursor animado, zoom no elemento, callouts |
| `glass-3d` | lançamento, feature premium | espaço escuro com blobs de gradiente; painéis de vidro fosco (Three.js `MeshPhysicalMaterial` com transmission) com a UI como textura | câmera voa entre painéis em posições 3D; whip entre passos |
| `clay-soft` | produto amigável, onboarding | estúdio off-white, materiais clay pastel com um acento | objetos se materializam por dissolve; câmera orbita levemente |
| `paper-editorial` | explicação conceitual, docs | papel com grade de pontos, recortes, marcador de texto (highlight sweep) | elementos caem e giram; marker sweep nas palavras-chave |
| `dark-tech` | dev tools, CLI, APIs | navy profundo, mono para rótulos, glow ciano/âmbar | linhas de dados, scan lines, terminal digitando |

Para 3D (`glass-3d`, `clay-soft`), siga a rota Three.js de `07-build-render.md` e o bloco 7 (acabamento) do prompt mestre.

## 4. Kit de componentes compartilhados (definir aqui, construir em T6)

Liste os componentes que todas as cenas usarão, com os tokens já aplicados:
- `Background` (mundo do estilo)
- `AppWindow` (moldura da janela/aparelho com o screenshot do passo; barra de título, raio, sombra)
- `Cursor` (seta + anel de clique; trajetória por curva, nunca linha reta teleportada)
- `FocusZoom` (zoom/punch-in no `target_box` com máscara suave ao redor)
- `Callout` (balão ou etiqueta ancorada no `target_box`, máx. 6 palavras)
- `StepChip` (indicador "Passo 2 de 5")
- `TitleCard` e `OutroCard` (logo, título, CTA)
- `Caption` (faixa de legenda no estilo escolhido em `09-acabamento.md`)
- `Redact` (blur ou substituição de dado sensível)

## Saída: `blueprint.md`

```markdown
# Blueprint — <título>
## Tokens
- Fundo / superfície / texto / acento: #… / #… / #… / #…
- Fontes: títulos <família, peso>, UI <família>, rótulos <mono?>
- Raio <px>, sombra <spec>
- Logo: assets/logo.svg
## Estilo
- Nome: <clean-product | …> (+ referência: <link>)
- Mundo: <1 frase>
- Câmera: <dentro da cena> / <entre cenas>
- Texto: <como entra e sai>
- Efeitos: <grão, glow, vinheta, bloom…>
- Ritmo: cena média <s>, transição <s>
## Componentes
- <lista acima com qualquer ajuste>
## Proibido
- <ex.: mais de um acento; texto < 28 px a 1080p; fundo preto puro>
```
