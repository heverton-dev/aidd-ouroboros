# 06 — Prompt mestre em 8 blocos (T6)

O prompt mestre é a especificação que o agente (ele mesmo, ou um subagente/modelo de build) segue para escrever a composição. Ele é **gerado** a partir de `brief.md`, `blueprint.md`, `storyboard.json` e `rules.md`, nunca escrito do zero. Salve em `composition/PROMPT.md`.

Estrutura derivada dos prompts mostrados no vídeo de referência (glassmorphism, clay e holográfico), adaptada a tutoriais de UI real. Os blocos vêm sempre nesta ordem.

## Bloco 1 — Cabeçalho técnico
"Faça um tutorial animado de <duração> s, <largura>×<altura>, <fps> fps, intitulado “<título>”, em HyperFrames (HTML + GSAP; Three.js só onde indicado). **Toda animação é função de um tempo t** (timeline pausada e buscável), para que o render frame a frame seja determinístico. Sem `Date.now()`, sem `Math.random()` sem semente, sem animação CSS fora da timeline."

## Bloco 2 — Mundo e estilo
Do `blueprint.md`: nome do estilo, fundo/mundo, materiais (para 3D: `MeshPhysicalMaterial` com transmission/roughness, sheen, `RoomEnvironment`), iluminação, paleta em hex e **um único acento**, raio/sombra das janelas. "Profissional, sleek, legível. Trate este vídeo como o showreel da sua candidatura a uma vaga de motion designer de produto."

## Bloco 3 — Camada de texto
"Texto como DOM/canvas 2D **acima** da cena (para 3D: desenhado depois do tone mapping). Títulos em <fonte>, rótulos de UI em <fonte da UI>, mínimo 28 px a 1080p (40 px em 9:16). Rótulos ancorados a elementos da tela usam o `target_box` (para 3D: posição projetada para a tela). Legendas são posicionadas depois, por cálculo, longe do foco; declare no `storyboard.json` (`focus_boxes`, em pixels do quadro) todo callout, chip, selo ou título que você desenhar, e mantenha `screen_box` e `zoom` iguais aos da composição."

## Bloco 4 — Câmera
"Câmera com keyframes de posição e alvo: deriva lenta dentro da cena (2 a 4 %), movimento rápido entre cenas (expo ease, 0,4 a 0,6 s). Os **elementos também se movem dentro da cena** (janela entra com leve rotação 3D, callouts sobem, cursor segue curvas). Zoom no `target_box` do passo ativo durante a ação."

## Bloco 5 — Cenas cronometradas
Uma linha por cena do `storyboard.json`, exatamente com os tempos:
"`<id> <Nome> (<start>–<end> s)`: <visual>. Texto na tela: “<on_screen_text>”. Narração: <arquivo de áudio>. Evidência: <screenshot(s)>. Saída: <transition_out>."
Cada cena tem um **verbo visual** (desliza, aproxima, clica, digita, conta, revela, dissolve) e algo diferente acontecendo; proibido repetir o mesmo fade/slide em todas.

## Bloco 6 — Elementos contínuos
Algo que atravessa todas as cenas e amarra a história: indicador de progresso "Passo n de N", linha/trilho que se desenha conforme os passos avançam, mesmo cursor, partículas de fundo afastadas do caminho da câmera.

## Bloco 7 — Acabamento
2D: grão leve (2 a 4 %), vinheta sutil, sombras suaves; glow só no acento.
3D: render target HDR half-float com MSAA 4×, bloom com threshold alto (só realces), tone mapping neutro ou ACES, passe final com grão, vinheta e aberração cromática muito leve; **clamp em todo valor que entra em `pow()`** para não gerar NaN.

## Bloco 8 — Verificação
"Antes do render completo: (1) rode `npx hyperframes check` e corrija todo erro; (2) gere stills de cada cena (`npx hyperframes snapshot --review`); (3) confira em cada still: todo texto dentro do quadro e legível, nada sobreposto, nada na faixa de legenda, nenhum dado sensível, cursor e zoom no elemento certo. Só então renderize."

## Regras do projeto (anexo obrigatório)
Cole o conteúdo de `rules.md` (seções Lições e Congelado) ao fim do prompt. Regras do projeto vencem preferências do prompt.

## Quando o usuário está aberto ("surpreenda-me")
Antes de escrever o prompt mestre, proponha **3 direções em texto** (estilo + ideia de câmera + elemento contínuo, 2 linhas cada) e deixe o usuário escolher. Só então gere o prompt.
