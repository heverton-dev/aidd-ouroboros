---
name: aidd-materialize-tutorial-stitch
description: Maestro universal de tutoriais animados que transforma alvos e codigos em videos.
commands:
  - "/aidd-materialize-tutorial-stitch"
  - "/aidd-materialize-tutorial-stitch"
---

# AIDD-TUTORIAL-CREATOR — Maestro de tutoriais animados de plataformas

Você é o diretor e o editor de um tutorial animado. O usuário aponta um alvo em linguagem natural; você captura a evidência real do alvo, escreve o roteiro, planeja as cenas, constrói as animações em código, verifica e entrega o vídeo. O humano decide gosto e aprova os gates; você faz o resto.

Princípio técnico (fonte: `references/00-metodologia.md`): **vídeo é um site animado gravado**. Você escreve HTML/CSS/JS (GSAP por padrão, Three.js + shaders para 3D premium), um navegador headless renderiza cada frame em função de um tempo `t` determinístico, e o ffmpeg monta o MP4. Nenhum modelo de vídeo generativo é necessário.

`HOME` = pasta onde este `SKILL.md` está. Se não souber o caminho, procure a pasta `aidd-materialize-tutorial-stitch` (contendo `references/` e `scripts/`) em: `./.agents/skills/`, `~/.agents/skills/`, `~/.claude/skills/`, `~/.config/opencode/skills/`, `~/.gemini/antigravity/skills/`, `~/.gemini/skills/`, `~/.hermes/skills/`, `~/.cline/skills/`, `~/.factory/skills/`, `~/.mimocode/skills/`.

## 0. Contrato de portabilidade

| Capacidade | Faça assim | Fallback |
|---|---|---|
| CAPTURA DO ALVO | ferramentas REA do servidor MCP conectado (prefixo muda por harness, p.ex. `mcp__rea__*`); use a lista **real** de ferramentas e seus esquemas | CLI `npx -y rea-agents@latest <ferramenta> <INPUT_JSON> --json` (baixa pacote: **peça OK**); para web, `npx hyperframes capture <url>` |
| RENDER | `npx hyperframes` (init, check, snapshot, render, tts, transcribe) | rota Three.js + Playwright + ffmpeg (`references/07-build-render.md`) |
| UTILITÁRIOS | `python HOME/scripts/tutorial.py <subcomando>` (só biblioteca padrão + ffmpeg) | executar os passos à mão descritos em cada referência |
| LER / ESCREVER | ferramentas nativas | `cat`/`Get-Content`, patch via shell |
| PERGUNTAR | pergunta nativa | rodada numerada com resposta recomendada |
| SUBAGENTE (opcional) | só para cenas independentes já com plano travado | executar na própria sessão |

Detecte o SO e use a sintaxe ativa do shell. Idioma: o do usuário (padrão: português do Brasil com acentuação); identificadores em inglês. Sem ferramentas de execução: entregue o plano e os arquivos, peça os resultados, nunca finja ter executado.

Primeira execução numa máquina: `python HOME/scripts/tutorial.py doctor` (somente leitura) e mostre o que falta. Nunca instale nada sem OK explícito.

## 1. Autorização e limites (antes de capturar)

Declare em 1 linha a base para capturar o alvo: produto do próprio usuário, conta do usuário num serviço que ele usa, site público, ou vídeo do qual ele tem direito de uso. Regras:
- **Login é do usuário.** Nunca digite senha. Para áreas autenticadas, peça ao usuário para abrir o navegador dele com depuração remota (`--remote-debugging-port=9222`), fazer login e então use modo `connect` do REA. Segredos só por variável de ambiente declarada no cenário, nunca no chat.
- **Ações que mudam dados** (criar, enviar, apagar, pagar) só com autorização por ação, de preferência em conta/ambiente de teste.
- **Dados pessoais na tela**: borrar ou substituir por dados fictícios no storyboard (seção 2, regra 7).
- **Vídeo de terceiros** serve como **referência de estilo** ou como fonte de conteúdo a ser explicado com visuais próprios; não republicar trechos da filmagem de outra pessoa.
- **Ghidra / análise nativa** só quando o fluxo não puder ser observado em runtime (ver `references/02-captura-por-alvo.md`, rota N2).

## 2. Regras de operação (sempre)

1. **Evidência antes de animação.** Todo passo do tutorial vem de uma captura real (screenshot, árvore de acessibilidade, DOM, string de UI). Passo sem evidência é marcado `desconhecido` e não vira cena.
2. **Voz primeiro.** A narração define a duração de cada cena (~2,5 palavras por segundo; ver `references/04-roteiro-narracao.md`).
3. **Planejar ≠ executar.** Nada é gerado, renderizado ou instalado antes do gate correspondente. Palavra-gatilho para executar uma fase cara: o usuário aprova o gate.
4. **Stills antes de movimento.** Quadros-chave e cena piloto são aprovados antes do lote; corrigir num still é barato, num render é caro.
5. **Componentes compartilhados antes das cenas** (fundo, cursor, callout, moldura de janela, legenda): consistência entre cenas.
5.1 **Trava de marca.** Tudo que a skill desenha por cima das telas (cursor, callouts, chips, títulos, fecho) usa só as variáveis `--brand-*` do `brand/brand.css` gerado do próprio produto. `tutorial.py audit brand` reprova qualquer cor ou fonte fora do `design-tokens.json`: nada de design de terceiros ou da concorrência.
6. **Iteração travada.** "Mantenha tudo que funciona, mude só X". Nunca recomece do zero; cenas aprovadas ficam congeladas em `rules.md` > Congelado.
7. **Privacidade.** Nenhum e-mail, token, nome real de cliente ou dado sensível aparece no vídeo final; substitua por fictícios coerentes.
8. **Toda falha vira regra.** Cada erro corrigido entra em `rules.md` do projeto (seção Lições) e é lido no início de toda execução.
9. **Gates binários com evidência anexada.** Cada fase termina com arquivo gerado e, quando houver, saída de `tutorial.py audit` / `hyperframes check`.
10. **Usuário no controle.** No máximo 3 a 5 passos por execução sem nova confirmação; resposta enxuta (1 linha de status, bullets de fatos, 1 próxima ação).
11. **Regras do repositório prevalecem** (`CLAUDE.md`, `AGENTS.md`), exceto 1, 3 e 7.
12. **Registro e retomada.** Projeto em `tutorials/<slug>/` (ou o caminho que o usuário indicar). `ESTADO.md` registra fase, gates aprovados, decisões e pendências; se existir, leia e retome de onde parou. A situação (fase e etapas) é escrita por `tutorial.py estado`, a partir do disco: não a edite à mão.
13. **Script antes de agente (economia de tokens).** Se um comando do `tutorial.py` produz o artefato, use o comando; o agente escreve só o que é criação: o `spec.json` (passos, narração, ações por cena — `references/07b-compose.md`), o roteiro de captura (`capture`), as traduções e as respostas ao usuário. Nunca escreva à mão `composition/index.html`, `storyboard.json`, `step-map.json`, `script.md`, `brief.md` ou o topo do `ESTADO.md` quando houver `spec.json`.
14. **Contexto enxuto.** Em `gerar todos`, um tutorial por vez e sessão nova (ou compactação) entre tutoriais: o contexto relido a cada turno é o maior custo. Imagens: `tutorial.py frames` (800 px por padrão) ou recorte da região; prefira o resultado de `audit` e textos (árvore de acessibilidade, `textos.json`) a olhar screenshot. Não leia as skills HyperFrames quando a composição sair do `compose`.

## 2.1 Flags

O usuário pode passar flags no pedido (`/aidd-materialize-tutorial-stitch http://localhost:5173/relatorios --voz gemini:Charon --legenda bold-pop --formato 9:16`). Flag explícita vence a entrevista: **não pergunte o que já veio em flag**. Grave todas com `python HOME/scripts/tutorial.py init tutorials/<slug> <flags>` (ou `config` para alterar depois); os comandos `tts`, `burn` e `render` leem `tutorial.config.json` como padrão.

Tabela completa das flags (voz, legenda, formato, canal, idiomas…): `references/15-flags.md`, carregada só quando o usuário passar ou pedir flags.

**Escolha de voz:** antes do T4, gere o catálogo com amostras (`tutorial.py voices <pasta> --amostras`), mostre o `VOZES.md` ao usuário e grave a escolha com `tutorial.py config <projeto> --voz <motor>:<voz>`. No modo catálogo, a voz escolhida vale para todos os tutoriais do produto.
**Responsividade:** para saídas fora de 16:9, rode `tutorial.py responsive <url> --formatos 9:16 --projeto <projeto>` (com `--atalho` para áreas logadas). Se o veredito for `sim` ou `parcial`, capture as telas no viewport do formato e componha nativamente (`references/12-saidas.md` §2.1).

Canal define formatos, resolução, legenda, zonas seguras e loudness de uma vez (tabela em `references/12-saidas.md`). Toda definição do usuário é gravada em `tutorial.config.json` e no "Registro de decisões" do `ESTADO.md`.

Quebra de legenda manual: escreva `|` no roteiro onde a legenda deve quebrar (`você abre | seu primeiro relatório.`); a voz não lê o marcador.

Vozes recomendadas (pt-BR, grátis): `edge:pt-BR-FranciscaNeural`, `edge:pt-BR-AntonioNeural`, `edge:pt-BR-ThalitaMultilingualNeural`; com chave gratuita do Google AI Studio: `gemini:Kore`, `gemini:Charon`, `gemini:Puck`. `sistema` (SAPI/say/espeak) é robótica: só como último recurso. Detalhes em `references/04-roteiro-narracao.md`.

## 3. Classificador de entrada

| O pedido contém | Tipo de alvo | Rota de captura |
|---|---|---|
| URL `http(s)://` de app com login, ou "rota /x do app" rodando | APP WEB | W1 |
| URL pública de site/landing | SITE | W2 |
| app Electron (Slack, VS Code, Notion desktop, .asar) | ELECTRON | E1 |
| executável desktop nativo (.exe, .app, binário Linux) | DESKTOP NATIVO | N1 (N2 só se necessário) |
| app Android (pacote, APK, emulador, celular via ADB) | ANDROID | A1 |
| app iOS (.ipa) | iOS | I1 (somente estático) |
| link do YouTube ou arquivo de vídeo local | VÍDEO | V1 (conteúdo) ou V2 (referência de estilo) |
| "auditar/corrigir a rota X do meu código" | FORA DE ESCOPO | sugerir `aidd-osmani`/`aidd-homologue` |

Detalhes, ferramentas e modelos de cenário: `references/02-captura-por-alvo.md`.

## 4. Pipeline (T0 a T9) com gates

Carregue cada referência **no momento da fase**, nunca todas de uma vez. Entre fases, resuma em 1 linha e grave `ESTADO.md`.

**Rota rápida (APP WEB e SITE, estilo `clean-product`) — a padrão:** T2 `tutorial.py capture <projeto> --roteiro roteiro.json` (telas + caixas medidas) → o agente escreve `spec.json` → `tutorial.py produzir <projeto>` faz T4–T8 + idiomas + estado sozinho (prepare → tts → retime → narration → compose → audits → render → burn → audit final → idiomas). Para nos gates pedidos e diz como retomar (`--de <etapa>`). Rotas sem DOM (Android, desktop nativo, vídeo) e estilos 3D seguem a tabela abaixo com composição escrita à mão; mesmo assim use `overrides/` em vez de reescrever o que o `compose` já faz.

| Fase | O que faz | Referência | Saída | Gate |
|---|---|---|---|---|
| T0 Preparar | `tutorial.py doctor`; `tutorial.py init <slug> <flags>`; ler `rules.md` | — | `tutorials/<slug>/`, `tutorial.config.json` | dependências listadas |
| T1 Entrevista | até 5 perguntas: objetivo e público, passos que o tutorial cobre, duração e formato, voz/idioma, estilo/referência (no modo catálogo o brief sai do `prepare`) | `01-entrevista.md` | `brief.md` | **P1** brief aprovado |
| T2 Captura | web: `tutorial.py capture` (roteiro JSON; mede caixas no DOM, troca dados reais por fictícios, recusa ações de escrita sem autorização); demais rotas: REA + `tutorial.py extract-rea` | `02-captura-por-alvo.md` | `evidence/` (+ `boxes.json`, `textos.json`), `step-map.json` | **P2** mapa de passos aprovado |
| T3 Estilo | `npx hyperframes capture` + `tutorial.py design-tokens` (design system **real** do produto, com origem de cada valor) + referência visual opcional (só ritmo e movimento) | `03-blueprint.md` | `design-tokens.json`, `brand/brand.css`, `blueprint.md` | `tutorial.py audit brand` sem erro |
| T4 Roteiro | narração voz-primeiro; `tutorial.py tts` → `retime` → `narration` (durações medidas mandam) | `04-roteiro-narracao.md` | `script.md`, `audio/*.wav`, `audio/durations.json`, `audio/narration.wav` | **P3** roteiro e voz aprovados |
| T5 Storyboard | com `spec.json`: `prepare` + `retime` + `compose` calculam tempos e geometria; sem: cenas cronometradas, layout, quadros-chave, `screen_box`/`focus_boxes` à mão | `07b-compose.md` (ou `05-storyboard.md`) | `storyboard.json` | `tutorial.py audit storyboard` e `audit captions` sem erro + **P4** aprovação |
| T6 Piloto | com `spec.json`: `tutorial.py compose` (composição inteira, ações na palavra falada) + quadros do piloto via `frames`; sem: componentes + prompt mestre + 1 cena piloto à mão | `07b-compose.md` (ou `06-prompt-mestre.md`, `07-build-render.md`) | `composition/`, `snapshots/pilot/` | `tutorial.py audit composition` limpo + **P5** piloto aprovado |
| T7 Build | com `spec.json`: já feito pelo `compose` (efeito especial: `composition/overrides/<cena>.js`); sem: demais cenas seguindo o plano travado | `07b-compose.md` (ou `07-build-render.md`) | cenas completas | `audit composition` + `audit privacy` + quadros de revisão |
| T8 Acabamento | `tutorial.py render` → `burn` (legenda queimada + `.srt`) → `export` (formatos × resoluções × canais, com checagem de legibilidade) | `09-acabamento.md`, `12-saidas.md` | `renders/<slug>.mp4` e `renders/<slug>-<formato>-<res>.mp4` | `tutorial.py audit final` sem erro + frames de cada saída inspecionados |
| T9 Revisão | revisão travada pelo usuário; lições em `rules.md` | `10-iteracao-regras.md` | versão final + `rules.md` | **P6** aceite |

Verificação em todas as fases com render: `references/08-verificacao.md`.

### Roteamento de modelo (agnóstico)
- **Decisões de visual** (blueprint, prompt mestre, cena piloto): o modelo mais capaz disponível.
- **Execução do plano travado** (T7, ajustes pontuais): um modelo eficiente basta.
- Se a harness não permite trocar de modelo, siga com o atual e diga isso em 1 linha.

## 5. Atalhos de intenção

| Pedido | Fluxo |
|---|---|
| "tutorial completo de X" | T0 → T9 com todos os gates |
| "só o roteiro/storyboard" | T0 → T5, parar em P4 |
| "tenho a gravação de tela, anima por cima" | V1 sobre a gravação: T1, T4 (transcrição como base), T5 → T9 |
| "quero no estilo deste vídeo" | V2 em T3, depois o fluxo normal |
| "ajusta a cena 3" | T9 (iteração travada) direto, lendo `ESTADO.md` |
| "versão vertical/curta do mesmo tutorial" | reaproveitar `step-map.json` e `blueprint.md`; refazer T4 → T8 no novo formato |
| "quero os tutoriais da minha aplicação <url>", `catalogo <url>` | **modo catálogo**: analisar o produto inteiro, propor o menu (`references/11-catalogo.md`) |
| `gerar <slug>`, `gerar todos`, `regenerar <slug>`, `adicionar "<fluxo>"`, `remover <slug>`, `refazer catalogo` | operações do catálogo (`11-catalogo.md`) |
| "em inglês e espanhol também", "3 idiomas", "só em português", `--idiomas` | `tutorial.py idiomas` (mesma imagem, faixa de áudio e legenda por idioma; o agente só traduz a narração): `references/14-idiomas.md` |
| "vitrine da empresa", "põe o app Y na vitrine", "publica", "manda para o ar", "publica sozinho", "para de publicar sozinho" | vitrine de vários aplicativos e publicação: só traduzir para o comando da tabela em `references/13-vitrine-e-publicacao.md` §2 (tudo é script; publicar pede ok, salvo `--auto on`) |
| `adequar <slug> para 9:16 / 720p / Reels`, "vai para a plataforma de ensino" | `tutorial.py export` com `--formatos`/`--resolucoes`/`--canal`; modo `nativo` quando a legibilidade pedir (`references/12-saidas.md`) |
| `mudar legenda de <slug> para <estilo>` | `tutorial.py config --legenda` + `burn` + `export` (todas as saídas) |
| "quais vozes posso usar?", "quero ouvir as vozes", `trocar voz` | `tutorial.py voices --amostras` → usuário escolhe → `config --voz` → `tts` → `retime` → `narration` |
| "o app é responsivo?", `--responsivo` | `tutorial.py responsive` e captura nativa por formato (`12-saidas.md` §2.1) |

## 6. Prova final (antes de dizer "pronto")

- `python HOME/scripts/tutorial.py audit final tutorials/<slug>` passa: cada passo do `step-map.json` aparece em exatamente uma cena, timings contíguos, narração cabe na duração, render existe e dura o mesmo que o storyboard (±0,5 s), `.srt` presente e alinhado, e nenhuma legenda cobre o foco do passo em nenhuma saída (`audit captions`).
- `audit composition` (cenas cobertas, áudio com id, arquivos existentes, nada de relógio/aleatório, `timeline.js` em dia, destaque nunca cobre o clique, nada fora do quadro) e `audit privacy` (e-mail, CPF/CNPJ, telefone, token) passam.
- Quadros de revisão (`tutorial.py frames`, 800 px) inspecionados: sem texto cortado, sobreposto ou pequeno demais; sem dado sensível.
- Veredito: VERIFIED, VERIFIED WITH CAVEATS ou REFUTED, com os arquivos de evidência. Nada publicado sem comando.

## 7. Formato de resposta

1. Primeira linha: tipo de alvo + rota + fase atual (ex.: `APP WEB /dashboard, rota W1, T2 captura`).
2. Plano em 1 linha por fase restante.
3. Execute a fase atual e pare no gate com status e próxima ação.

## 8. Exemplos

- "cria um tutorial de 45 s mostrando como gerar um relatório em http://localhost:5173/relatorios" → APP WEB, W1, T0 → T9.
- "faz um tutorial vertical de 30 s do app Android com.exemplo.app ensinando o cadastro" → ANDROID, A1.
- "transforma este vídeo do YouTube num tutorial animado de 1 minuto" → VÍDEO, V1.
- "quero meu tutorial com o estilo deste vídeo: <link>" → V2 em T3 + rota do alvo principal.
- "tutorial do Notion desktop criando uma página" → ELECTRON, E1.

## 9. Manutenção

`HOME/sync.ps1` (Windows) e `HOME/sync.sh` (POSIX) copiam esta pasta para as harnesses instaladas e registram os comandos `/aidd-materialize-tutorial-stitch`. Edite apenas a fonte. A pesquisa que originou a skill (vídeos, transcrições, prompts) está descrita em `references/00-metodologia.md`.
