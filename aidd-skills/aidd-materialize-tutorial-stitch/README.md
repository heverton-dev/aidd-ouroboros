# aidd-tutorial-creator

Skill agnóstica que transforma um pedido em linguagem natural ("cria um tutorial de 45 s mostrando como gerar um relatório em http://localhost:5173/relatorios") num **tutorial animado completo em MP4**, com narração neural, legendas queimadas e `.srt`, a partir de evidência real da plataforma.

Funciona em qualquer harness ou CLI que leia arquivos e rode shell: Claude Code, Codex, Gemini CLI, OpenCode, Antigravity, Cursor, Cline, Kiro, Hermes, MimoCode.

> Manual completo: [`docs/MANUAL.md`](docs/MANUAL.md) (também em [`docs/MANUAL.pdf`](docs/MANUAL.pdf)).

## Como funciona, em uma frase

**Vídeo é um site animado gravado.** O agente captura as telas reais do alvo com o REA, escreve o roteiro, gera a voz, monta as cenas em HTML/GSAP (Three.js para 3D) com HyperFrames, renderiza frame a frame de forma determinística, queima as legendas e audita o resultado antes de entregar.

## O que ele aceita como alvo

| Alvo | Como é capturado |
|---|---|
| Rota de app web (com ou sem login) | REA `capture_browser_scenario` (seu login, nunca sua senha) |
| Site público | `hyperframes capture` + REA |
| App Electron (Slack, VS Code, Notion…) | REA via CDP + análise estática do `.asar` |
| App desktop nativo | REA (macOS) ou gravação da janela + extração de frames; Ghidra só se necessário |
| App Android | REA via ADB (emulador ou aparelho) |
| App iOS | análise estática do `.ipa` + gravação de tela sua |
| Vídeo do YouTube ou arquivo local | download, transcrição e frames, como conteúdo ou como referência de estilo |

## Início rápido

```bash
# 1. instalar nas harnesses desta máquina (Windows / macOS-Linux)
powershell -File sync.ps1
sh sync.sh

# 2. verificar dependências (somente leitura)
python scripts/tutorial.py doctor
```

Depois, na harness:

```text
/aidd-tutorial-creator cria um tutorial de 40 s do fluxo de exportação em http://localhost:5173/relatorios --voz edge:pt-BR-FranciscaNeural --legenda highlight
```

O agente conduz 10 fases (T0 a T9) e para em 6 pontos de aprovação: brief, mapa de passos, roteiro e voz, storyboard, cena piloto e aceite final.

## Flags principais

| Flag | Valores | Padrão |
|---|---|---|
| `--voz` | `edge[:voz]`, `gemini[:voz]`, `fish[:id]`, `kokoro[:voz]`, `sistema`, `nenhuma`, `gravacao` | `auto` (edge → gemini → kokoro → sistema) |
| `--legenda` | `highlight`, `bold-pop`, `word-by-word`, `clean`, `boxed`, `nenhuma` | `highlight` (16:9) / `bold-pop` (9:16) |
| `--legenda-posicao` / `--legenda-tamanho` | `auto`/`base`/`meio`/`topo` · `p`/`m`/`g` | `auto` · `m` |
| `--formato` | `16:9`, `9:16`, `1:1`, `4:5` | `16:9` |
| `--estilo` | `clean-product`, `glass-3d`, `clay-soft`, `paper-editorial`, `dark-tech` | `clean-product` |
| `--gates` | `todos`, `essenciais`, `nenhum` | `todos` |
| `--canal` | `instagram-reels`, `tiktok`, `youtube`, `plataforma-ensino`, `linkedin`, `whatsapp`… | — |
| `--formatos` / `--resolucoes` | `16:9,9:16,1:1,4:5` · `480p,720p,1080p` | formato principal · `1080p` |
| `--responsivo` | `auto`, `sim`, `nao` (tela real de celular/tablet nos formatos verticais) | `auto` |

**Vozes:** `tutorial.py voices <pasta> --amostras` gera o `VOZES.md` com amostras em áudio para você ouvir e escolher.
**Responsividade:** `tutorial.py responsive <url> --formatos 9:16` testa o app em cada tamanho; com `auto`, o vídeo vertical usa a tela real de celular quando o app é responsivo.

**Rota rápida (app web):** `tutorial.py capture --roteiro` fotografa as telas e mede as caixas no DOM; o agente escreve só o `spec.json` (passos, narração e ações por cena) e `tutorial.py produzir` faz o resto — voz, composição sem HTML à mão, auditorias (storyboard, legenda, composição, privacidade), render, legenda, idiomas e estado. Mesma spec, mesmo vídeo ([`references/07b-compose.md`](references/07b-compose.md)).
**Modo catálogo:** "quero os tutoriais da minha aplicação <url>" → a skill mapeia o produto (só observando), propõe o menu em `CATALOGO.md` e atende `gerar <pasta>`, `gerar todos`, `regenerar`, `adicionar`, `remover`, `refazer catalogo`.
**Vitrine da empresa:** vários aplicativos (cada um com seu catálogo) numa página estilo streaming só. `tutorial.py empresa add-app` junta, `tutorial.py vitrine` monta e `tutorial.py publicar` envia à VPS só o que mudou; `publicar --auto on` faz cada tutorial novo ir ao ar sozinho ([`references/13-vitrine-e-publicacao.md`](references/13-vitrine-e-publicacao.md)).
**Idiomas:** `tutorial.py idiomas` põe narração e legenda em pt-BR, en-US e es (padrão, configurável) sobre a mesma imagem; na vitrine, o player troca áudio e legenda como num serviço de streaming. O agente só traduz a narração ([`references/14-idiomas.md`](references/14-idiomas.md)).
**Adequação:** qualquer tutorial pode ganhar novos formatos, resoluções ou outra legenda depois de pronto (`tutorial.py export`), com checagem de legibilidade e registro no `ESTADO.md`.

Lista completa (21 flags) no [manual](docs/MANUAL.md#5-flags-referência-completa) e na seção 2.1 do [`SKILL.md`](SKILL.md).

## Requisitos

| Obrigatório | Opcional |
|---|---|
| Python 3.10+ (só biblioteca padrão nos scripts) | `GEMINI_API_KEY` (voz Gemini, grátis no Google AI Studio) |
| ffmpeg com libass | `FISH_API_KEY` (voz Fish Audio) |
| Node.js + `npx hyperframes` | `kokoro-onnx` + `soundfile` (voz local) |
| REA (MCP `rea` ou `npx rea-agents`) | `adb` (Android), Ghidra (análise nativa) |
| `edge-tts` (voz neural grátis) | `faster-whisper` (tempos por palavra dos motores sem marcação) |
| Chrome ou Edge | `yt-dlp` (vídeos de referência) |
|  | `playwright` para Python (`tutorial.py capture`) |

## Estrutura

```text
aidd-tutorial-creator/
├── SKILL.md                 maestro: roteamento, pipeline T0–T9, gates, flags
├── README.md                este arquivo
├── docs/MANUAL.md|.pdf      manual completo (regere o PDF com: python docs/build_manual.py)
├── references/              00–15 (+07b): metodologia, entrevista, captura, blueprint, roteiro,
│                            storyboard, prompt mestre, build/render, verificação,
│                            acabamento, iteração, catálogo, saídas, vitrine e publicação
├── scripts/tutorial.py      31 subcomandos (doctor, init, capture, prepare, compose, produzir, estado, tts, idiomas, export, catalog, vitrine, publicar, audit…)
├── scripts/compose.py       motor da composição (spec.json → composition/index.html), sem dependências
├── scripts/capture.py       captura por roteiro JSON (Playwright): telas, caixas e textos do DOM
├── scripts/explore.py       mapeamento passivo de um produto por perfil (modo catálogo)
├── scripts/responsive.mjs   medidor de responsividade (Playwright do REA, só leitura)
├── templates/               cenário REA, step-map, storyboard, rules, ESTADO, vitrine.html, vendor/hls.min.js (o config é gerado pelo init)
├── commands/                /aidd-tutorial-creator para Claude, Gemini e Antigravity
├── sync.ps1 · sync.sh       instalação global nas harnesses
```

## Estado da validação

| Item | Status |
|---|---|
| Pipeline web completo (captura REA → voz → composição → render → legendas → auditoria) | testado de ponta a ponta |
| Voz `edge` (pt-BR) e voz do sistema | testadas |
| 5 estilos de legenda, posição, tamanho e quebra manual | testados |
| Auditorias reprovam projeto sabotado | testado (9 sabotagens detectadas) |
| Design system real + trava de marca | testado no app real cadastros.vpsconexao.org (3 sabotagens detectadas) |
| Modo catálogo (5 perfis mapeados, 16 tutoriais propostos) | testado no mesmo app |
| Saídas 16:9 720p/480p, 9:16 e 1:1 (escalar, reenquadrar e nativo com telas de celular), legibilidade medida | testadas; `gerar todos` em lote ainda não exercitado |
| Catálogo de vozes e medidor de responsividade | testados no laboratório |
| Vozes `gemini`, `fish`, `kokoro` | implementadas, não testadas (sem chave/pacote nesta máquina) |
| Rotas Electron, desktop nativo, Android, iOS, comando `record` | documentadas, não testadas |

## Origem

Metodologia condensada de 9 vídeos de referência (Matt Penny, kaye.creatives, @theguneytopcu e outros), transcritos localmente. Fontes e princípios em [`references/00-metodologia.md`](references/00-metodologia.md).
