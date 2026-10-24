# 02 — Captura por alvo (T2)

Objetivo: para cada passo do tutorial, obter **evidência real**: um screenshot nítido do estado da tela, os textos visíveis (acessibilidade ou DOM) e a posição do elemento com que o usuário interage. A saída é `evidence/` + `step-map.json`.

Regras comuns:
- Use a **lista real** de ferramentas do REA conectado; os nomes abaixo são os do MCP `rea` (prefixo muda por harness). Sem MCP: `npx -y rea-agents@latest <nome-em-kebab-case> <INPUT_JSON> --json` (peça OK, baixa pacote).
- Capture na **resolução final do vídeo ou maior** (`device_scale_factor: 2` para zooms nítidos).
- Salve os PNGs com `python HOME/scripts/tutorial.py extract-rea <resultado.json> tutorials/<slug>/evidence/` (decodifica imagens inline do Evidence e nomeia por `step_id`).
- Ações que gravam dados exigem autorização por ação (SKILL.md, seção 1).
- Passo que não pôde ser capturado: registre `"evidence": "unknown"` e o motivo; não invente a tela.

## W1 — APP WEB (rota de aplicação, com ou sem login)

**Rota rápida (padrão quando o app tem atalho de teste ou é público): `tutorial.py capture`.** O agente escreve só o
roteiro; o script fotografa a página inteira, mede as caixas no DOM (`boxes.json`, nada de estimar olhando imagem),
guarda o texto de cada elemento (`textos.json` → `ui_text`) e troca dados reais por fictícios antes da foto.

```json
{"entrar": {"clicar": {"papel": "button", "nome": "Consultor"}},
 "ficticios": {"Nome Real Ltda": "Clínica Exemplo Ltda"}, "ficticios_rx": [["\\d{3}\\.\\d{3}\\.\\d{3}-\\d{2}", "000.000.000-00"]],
 "passos": [
  {"capturar": "home", "caixas": {"busca": {"papel": "searchbox"}, "csv": {"papel": "button", "nome": "CSV"},
                                   "card1": {"texto": "Visualizar Detalhes", "subir": "cartao"}}},
  {"clicar": {"papel": "button", "nome": "Visualização em Lista"}},
  {"capturar": "lista", "caixas": {"tabela": {"css": "table"}}},
  {"selecionar": {"papel": "combobox", "nome": "Status"}, "opcao": "Todos os status"},
  {"ir": "/templates"}, {"capturar": "templates"}]}
```

```bash
python HOME/scripts/tutorial.py capture <tutorial> --roteiro roteiro.json   # base = produto.url do catálogo
```

- Nomes **exatos** por padrão (`"exato": false` só com motivo): um nome parcial ("Lista") já casou com
  "Inativar Ana**lista**…" e inativou uma conta. Antes de clicar, o script lê o texto real do elemento e **recusa**
  qualquer coisa com cara de escrita (salvar, enviar, gerar, inativar, excluir, sair…) sem `"autorizado": true` no
  passo — e esse campo só entra com a autorização do usuário para aquela ação.
- Caixas viram nomes `"<captura>:<elemento>"` usados direto no `spec.json` (`07b-compose.md`).
- Login com senha não existe aqui: sem atalho de teste, use o modo `connect` do REA abaixo.

1. **Sem login** (ou app local `localhost`): modo `launch`. Peça ou detecte o executável do Chrome/Edge (`tutorial.py doctor` lista os caminhos).
2. **Com login**: o usuário abre o próprio navegador com depuração remota e faz login:
   - Windows: `"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir=%TEMP%\tc-profile`
   - macOS: `open -na "Google Chrome" --args --remote-debugging-port=9222 --user-data-dir=/tmp/tc-profile`
   - Linux: `google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/tc-profile`
   Depois: `list_browser_targets` com `{"cdp_endpoint": "http://127.0.0.1:9222"}` → escolha o `target_id` da aba do app → modo `connect`.
3. **Reconhecimento passivo** (antes de agir): `inspect_web_page` com `include_accessibility_text: true` na aba alvo. Use para descobrir rótulos e papéis reais dos controles (localizadores `role` + `name` são os mais estáveis).
4. **Cenário do fluxo**: `capture_browser_scenario` com uma ação por passo do tutorial e `capture.after_each_step: ["screenshot", "accessibility"]`. Modelo em `templates/browser-scenario.json`. Pontos de atenção:
   - **`after_each_step` captura a tela DEPOIS da ação.** A tela "antes do clique" de um passo é a captura do passo anterior (ou o `initial`/`scenario_start` para o primeiro). Registre as duas em `step-map.json` (`evidence_before` e `evidence`) e mostre o antes durante a ação e o depois no clique; mostrar o "depois" antes do clique é o erro mais comum.
   - Resultados grandes (screenshots inline): prefira o CLI do REA com saída em arquivo (`rea capture-browser-scenario cenario.json --json > capture.json`; o pacote já instalado pelo MCP fica em `node_modules/rea-agents/scripts/rea.mjs`) para não inflar o contexto da harness.
   - Depois de cada clique que muda a tela sem mudar a URL, inclua um `wait_for` do estado pronto (seletor do resultado visível).
   - `environment.locale` = idioma do tutorial (ex.: `pt-BR`), `viewport` = resolução de captura, `reduced_motion: "reduce"` para telas estáveis.
   - Valores digitados em formulários são **fictícios** (`source: "literal"`); segredos só como `source: "secret"` com `secrets[].environment_variable`.
5. **Posição dos elementos**: o `accessibility`/`dom` de cada passo dá o texto; a caixa do elemento (x, y, w, h) é necessária para cursor, zoom e callout. Obtenha-a por (a) `hyperframes capture` da mesma URL, que exporta componentes com geometria, ou (b) leitura visual do screenshot, registrando a caixa aproximada em `step-map.json` > `target_box`. Marque `box_source: "visual"` quando for estimada.
6. **Tokens visuais**: `npx hyperframes capture <url> -o tutorials/<slug>/capture --json` (somente páginas sem login ou acessíveis ao Chrome do agente) gera screenshots, cores, fontes e componentes editáveis. Para páginas com login, extraia tokens do DOM/CSS observado (`inspect_web_page`) e dos screenshots.

## W2 — SITE (página pública, landing, documentação)

- `npx hyperframes capture <url> -o tutorials/<slug>/capture --json` é a primeira ferramenta: captura até 21 telas, ativos, tokens e componentes HTML reutilizáveis.
- Rolagem e seções: `capture_browser_scenario` em `launch` com `goto` + `wait_for_timeout` e screenshots por passo; para página longa, um passo por seção (âncoras `#secao` no `goto`).
- Bundle do site (para entender um widget/animação que você quer recriar): `analyze_web_bundle`, `trace_web_module_imports`.

## E1 — ELECTRON (Slack, VS Code, Notion desktop, app próprio)

1. **Telas**: Electron é Chromium. Peça ao usuário para iniciar o app com `--remote-debugging-port=9223` (atalho ou terminal) e faça login nele. Então:
   - `list_electron_targets` / `list_browser_targets` com `http://127.0.0.1:9223` → `target_id` da janela principal;
   - `capture_browser_scenario` em modo `connect` (mesmo contrato do W1) para o fluxo com screenshots por passo, ou `capture_web_screenshot` para um still do estado atual.
2. **Entender a estrutura** (menus, rotas internas, nomes de telas) sem executar: `analyze_javascript_application` no `.asar` ou na pasta `resources/app` (estático, não precisa de MCP: `npx -y rea-agents@latest analyze-javascript-application <caminho> --json`).
3. **Comportamento que só aparece ao executar** (deep link, segunda instância, IPC): `capture_electron_scenario` com `executable_path` e `application_path` absolutos. Ele devolve evidência de janelas/IPC, **não** screenshots; combine com o passo 1 para as imagens.

## N1 — DESKTOP NATIVO (Windows, macOS, Linux)

1. **macOS**: `observe_native_ui` (árvore de acessibilidade + screenshot da janela por `pid` e `window_id`) e `capture_native_ui_scenario` (clique, rolagem, digitação por caminho de acessibilidade, com capturas antes/depois). Exige permissão de Acessibilidade e Gravação de Tela concedida pelo usuário.
2. **Windows e Linux** (ou quando o REA não cobre a UI nativa): grave a tela da janela enquanto o **usuário** executa o fluxo, e o agente cria os stills a partir da gravação:
   - `python HOME/scripts/tutorial.py record --window "<título da janela>" --seconds 60 --out evidence/raw.mp4` (Windows: ffmpeg `gdigrab`; Linux: `x11grab`; macOS: `avfoundation`).
   - `python HOME/scripts/tutorial.py frames evidence/raw.mp4 --scene 0.25 --out evidence/frames/` extrai um frame por mudança de tela; o agente escolhe um frame por passo e registra em `step-map.json`.
3. **Textos da UI** (rótulos de menus e botões, para roteiro e callouts): leia dos screenshots; quando estiverem ilegíveis ou o app for localizado, use a rota N2.

## N2 — Análise estática do binário (somente se necessário)

Use **apenas** quando um passo do tutorial depende de algo que não aparece observando a UI: nome exato de menu oculto, atalho de teclado não documentado, tela que só abre por configuração, textos de diálogo localizados.
- `open_binary` no executável → `list_strings` / `search_strings` (rótulos, atalhos, mensagens) → `xrefs` para a função que monta a tela, se precisar entender a condição.
- Provider nativo: o REA usa o provider configurado (Hopper, IDA ou **Ghidra**: `GHIDRA_INSTALL_DIR` ou `analyzeHeadless` no PATH). Se nenhum estiver configurado, informe e siga com N1.
- Registre o achado como `"evidence": "static:<evidence_id>"` e rotule como **derivação**, não observação. Nada de decompilado aparece no vídeo.

## A1 — ANDROID (emulador ou aparelho via ADB)

1. `list_adb_devices` → `serial`; `resolve_adb_packages` ou `list_adb_packages` para achar o pacote.
2. `start_adb_app` (`serial`, `package`) para abrir o app (muta o estado do aparelho: peça OK).
3. O **usuário** executa cada passo no aparelho (ou o agente via `start_adb_activity` para telas diretas); a cada passo: `capture_adb_screen` (`serial`, `output_directory` novo por passo, p.ex. `evidence/step-03/`) e `inspect_adb_window` (qual Activity está em foco, para nomear a tela).
4. Estrutura do app sem executar (nomes de telas, textos, ícones): `pull_adb_package` → `inspect_android_package` → `decode_android_resources` (strings localizadas, cores, ícones vetoriais).
5. Formato: telas de celular pedem vídeo 9:16 ou moldura de aparelho em 16:9 (layout `device-frame`, ver `05-storyboard.md`).

## I1 — iOS (somente estático)

Sem captura ao vivo. Com o `.ipa` do próprio usuário: `open_binary` → `inspect_asset_catalog` (ícones, cores), `decode_interface_builder` (telas e textos de storyboards/xibs), `inspect_plist`. Para as telas reais, peça ao usuário gravações de tela do iPhone (Controle → Gravação) e siga como N1 passo 2 (`tutorial.py frames`).

## V1 — VÍDEO como conteúdo (YouTube ou arquivo local)

O vídeo é a fonte do conteúdo: uma gravação de tela crua, uma aula longa a ser condensada, ou a demo do próprio usuário.
1. `python HOME/scripts/tutorial.py reference <url-ou-arquivo> --out tutorials/<slug>/source/` baixa (yt-dlp), extrai áudio, transcreve com timestamps (`faster-whisper` ou `npx hyperframes transcribe`) e tira frames por mudança de cena + uma folha de contato.
2. O agente lê transcrição + frames e monta `step-map.json`: cada passo com o trecho de fala (`source_span`) e o frame que o ilustra.
3. Direitos: se o vídeo não é do usuário, ele vira **roteiro e referência**; os visuais do tutorial são recriados (UI real capturada por W1/E1/N1/A1 ou ilustração em código), nunca recortes da filmagem de terceiros.

## V2 — VÍDEO como referência de estilo

1. Mesmo comando `reference` (frames a cada ~1 s ou por cena + transcrição).
2. O agente atua como **analista frame a frame** e escreve `blueprint.md` > Referência: paleta (hex), tipografia, ritmo (duração média de cena, cortes por minuto), movimentos de câmera, transições, tratamento de texto, efeitos (grão, glow, blur), layouts recorrentes. **Só palavras de estilo; nunca a história.**
3. Detalhes do blueprint: `03-blueprint.md`.

## Saída: `step-map.json`

Esquema completo em `templates/step-map.json`. Campos por passo:

```json
{
  "id": "s03",
  "title": "Filtrar por período",
  "user_action": "clicar em 'Período' e escolher 'Últimos 30 dias'",
  "result": "a tabela recarrega com 30 dias",
  "screen": "Relatórios",
  "evidence_before": "evidence/s02.png",
  "evidence": "evidence/s03.png",
  "box_source": "capture | visual | accessibility",
  "target_box": [1210, 188, 164, 40],
  "ui_text": ["Período", "Últimos 30 dias"],
  "sensitive": ["coluna Cliente"],
  "notes": ""
}
```

Gate **P2**: mostre a lista de passos (id, título, ação, resultado) com o caminho de cada evidência; o usuário confirma ordem e escopo. Passos `unknown` ficam fora até serem resolvidos.
