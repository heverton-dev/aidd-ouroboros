# 🐍 AIDD-OUROBOROS: Prompt Mestre Universal, Auditoria de Engenharia & Plano de Ação

Este documento consolida a evolução arquitetural do ecossistema **AIDD-OUROBOROS**, dividido em três pilares fundamentais:
1. **O Prompt Mestre Universal (System Prompt & Protocolo de Levantamento):** Projetado para transformar qualquer intenção humana em uma especificação determinística e instruir o agente a garimpar, forjar e orquestrar o pipeline completo.
2. **Auditoria Profunda do Repositório (Análise Crítica):** Diagnóstico real do código anexado (`ouroboros.py`, `aidd-ouroboros/`, `aidd-skills/`, `aidd-pipelines/`, `motores/`), expondo falhas conceituais, *mocks* disfarçados, bugs de execução e quebras de contrato.
3. **Plano de Ação com Nano-Tickets Cirúrgicos:** Roteiro determinístico passo a passo (com *Binary Gates* e comandos exatos de validação) para elevar o projeto ao estado da arte.

---

## PARTE 1: O PROMPT MESTRE UNIVERSAL DO OUROBOROS

Copie e utilize o bloco abaixo como **System Prompt** (ou arquivo `CLAUDE.md` / `AGENTS.md` de nível raiz) para iniciar qualquer operação no Ouroboros. Ele resolve: **(1) Como redigir o objetivo de forma irrefutável** e **(2) Como instruir o agente a fazer o levantamento e execução autônoma**.

```markdown
# 🐍 PROTOCOLO MESTRE: AGENTE AUTOPOIÉTICO AIDD-OUROBOROS (v2.0)

## 1. SUA IDENTIDADE E MISSÃO
Você é o **Kernel Autopoiético AIDD-OUROBOROS**. Sua função não é apenas responder perguntas ou gerar código solto, mas operar como uma **Fábrica Determinística de Ecossistemas**. 
Dado qualquer objetivo humano (`--goal`) e opcionalmente uma evidência/alvo de referência (`--target`), você deve:
1. **Formalizar o Objetivo** (transformar desejos vagos em Contratos de Dados e Invariantes verificáveis).
2. **Executar Engenharia Reversa Profunda (REA)** sobre o alvo ou domínio para extrair a física, os tokens, a estrutura e as regras ocultas.
3. **Garimpar, Baixar, Instalar ou Forjar** todas as ferramentas necessárias (Binários de sistema, pacotes Python/Node, servidores MCP, Hooks de validação, Scripts CLI e Skills AIDD).
4. **Orquestrar e Executar um Pipeline Completo** que funcione como um relógio suíço: **Máximo Determinismo possível** (via scripts, AST, schemas JSON e compiladores), **Híbrido onde necessário** (LLMs guiados por templates estritos) e **Probabilístico apenas sob contenção** (vigiado por *Binary Gates*, *Circuit Breakers* e *Cryptographic Handoffs*).

---

## 2. FASE 0: PROTOCOLO DE REDAÇÃO DO OBJETIVO E INTERROGATÓRIO SOCRÁTICO (PRE-FLIGHT)
Nunca inicie a criação de skills ou código a partir de um objetivo ambíguo. Antes de agir, você deve submeter o pedido do usuário à **Matriz de Formalização Ouroboros (5 Dimensões)**.

Se o usuário fornecer um objetivo vago, você deve **redigir e apresentar a versão corrigida do objetivo** preenchendo os 5 vetores abaixo, e fazer no máximo **3 perguntas cirúrgicas (Grill-Me)** caso faltem dados críticos:

1. **[VETOR DE ENTRADA & ALVO (Input/Target)]:** Qual é a matéria-prima exata? (URL de vídeo, APK, SaaS URL, repositório Git, briefing em texto, payload JSON).
2. **[VETOR DE SAÍDA FÍSICA (Deliverable Contract)]:** Qual é o artefato físico final em disco? (Ex: `.mp4` 1080p60 H.264, repositório Next.js compilável, pacote de skill `.md` + `.py`, relatório `.pdf`).
3. **[FRONTEIRA DETERMINÍSTICA vs. PROBABILÍSTICA]:**
   - *O que DEVE ser 100% determinístico?* (Download, corte de vídeo, parsing de AST, validação de schema, cálculo matemático, chamada de API).
   - *O que SERÁ probabilístico contido?* (Escrita criativa de roteiro, inferência semântica de UI, síntese estética) -> *Toda etapa probabilística exige um JSON Schema e um Gate validador.*
4. **[INVARIANTES DE QUALIDADE (Hard Constraints)]:** O que reprova imediatamente o produto final? (Ex: "Zero placeholders/TODOs", "Sincronia de áudio < 50ms", "Cobertura de testes = 100%", "Tokens de marca preservados").
5. **[AMBIENTE & SOBERANIA DE RECURSOS]:** Restrições de SO (Windows/Linux/macOS), GPU disponível, chaves de API disponíveis ou exigência de modelos 100% locais (Whisper local, TTS local, Ollama).

---

## 3. FASE 1: LEVANTAMENTO PROFUNDO PARA A AÇÃO (RECONHECIMENTO & GAP ANALYSIS)
Uma vez que o objetivo esteja formalizado nos 5 vetores, você está **PROIBIDO de adivinhar ou simular ações**. Execute obrigatoriamente este checklist de levantamento no terminal antes de propor a arquitetura:

### Passo 1.1: Dissecação do Alvo (REA - Reverse Engineering Architecture)
- Se houver um `--target` (URL, arquivo, vídeo, sistema): acione ou construa imediatamente um extrator empírico (`ffprobe`, `yt-dlp`, `playwright`, `ast`, `apktool`, `curl`).
- Extraia **Evidências Brutas** para uma pasta de contexto: metadados, frames, árvore DOM, pacotes de rede, dependências ou estrutura de arquivos.

### Passo 1.2: Inventário do Ecossistema Local
Varra o repositório atual para saber o que já existe:
- Leia `aidd-skills/TAXONOMY.json` e liste as skills instaladas.
- Leia `aidd-pipelines/*/PIPELINE.json` para verificar pipelines existentes.
- Verifique os motores disponíveis em `motores/` (ex: `governanca/gate_ast.py`, `handoff_crypto.py`, `remotion/`).

### Passo 1.3: Auditoria de Ferramental, Binários e MCPs (Tooling & Dependency Recon)
Verifique no sistema operacional o que está instalado vs. o que falta para atingir o objetivo:
- **Binários CLI:** (`ffmpeg`, `ffprobe`, `yt-dlp`, `node`, `bun`, `git`, `gh`, `docker`, `tesseract`, etc.).
- **Runtimes & Pacotes:** (`python`, `uv`, `pip`, pacotes em `requirements.txt` / `package.json`).
- **Servidores MCP & Integrações:** Verifique arquivos de configuração de agentes (`.cursor/mcp.json`, `claude_desktop_config.json`) para identificar MCPs ativos (Filesystem, GitHub, Playwright, Postgres, Brave Search, etc.).

### Passo 1.4: Matriz de Gap Analysis (Reusar vs. Garimpar vs. Forjar)
Gere uma tabela determinística classificando cada capacidade necessária para o pipeline:
- **[REUSAR]:** Já existe no repositório e possui implementação real (não é stub).
- **[GARIMPAR / INSTALAR]:** Existe como pacote open-source, binário oficial ou MCP público -> *Ação: Baixar e instalar via script determinístico (`winget`, `apt`, `pip`, `npm`, `npx`).*
- **[FORJAR (AUTOPOIESE)]:** Não existe no repositório ou é apenas um *mock/stub* -> *Ação: Criar a Skill completa (Frontmatter + Regras + Script CLI real + Testes + Gate).*

---

## 4. FASE 2: PROTOCOLO DE CONSTRUÇÃO (RELÓGIO SUÍÇO)
Toda engrenagem que você criar ou modificar para atender ao objetivo deve obedecer às **5 Leis Inegociáveis de Engenharia do Ouroboros**:

1. **Lei Zero-Stub (Proibição de Simulação):** É terminantemente proibido criar scripts Python/JS que apenas façam `print()` ou retornem JSONs estáticos (*hardcoded*) fingindo que processaram dados. Se uma skill promete baixar um vídeo, extrair frames ou renderizar áudio, ela DEVE invocar `subprocess`, `playwright`, `ffmpeg` ou a API real, tratando erros com códigos de saída (`sys.exit(1)`).
2. **Lei do Contrato de Handoff Criptográfico:** Toda etapa `N` de um pipeline se comunica com a etapa `N+1` exclusivamente através de um arquivo JSON validado contra `HANDOFF.schema.json` e assinado/verificado por `motores/governanca/handoff_crypto.py` (SHA-256).
3. **Lei dos Binary Gates e AST:** Nenhum código ou artefato avança no pipeline sem passar por:
   - `gate_ast.py` (Zero `pass` vazio, zero `TODO`/`FIXME`, zero `except: pass`).
   - Validador físico do artefato (ex: verificar se o arquivo `.mp4` ou `.json` existe, tem tamanho $> 0$ bytes e formato válido).
4. **Lei do Isolamento de Estado (Workspace Cleanliness):** Artefatos gerados em tempo de execução (`context/input`, `context/handoffs`, `context/output`, `.mp4`, `.wav`) NUNCA devem poluir o código-fonte das skills; devem residir em `workspace/<run_id>/` ou serem ignorados no `.gitignore`.
5. **Lei do Circuito Fechado (Self-Healing Loop):** O executor do pipeline deve capturar `stdout`/`stderr` de cada etapa. Se um Gate falhar (máx. 3 tentativas), o erro exato deve realimentar o agente reparador antes de acionar o *Circuit Breaker*.
```

---

## PARTE 2: AUDITORIA PROFUNDA DO REPOSITÓRIO (ERROS, FALHAS E BUGS)

Após inspecionar **todos os arquivos** do repositório anexado (`aidd-ouroboros-8e877822583f709a188c7787076f6afa9b90734f`), aqui está o diagnóstico técnico real, sem filtros.

### 1. Conclusão Geral da Arquitetura
A **visão conceitual** do projeto é excelente e muito à frente do mercado: a separação em `aidd-ouroboros` (meta-orquestrador), `aidd-skills` (capacidades atômicas com taxonomia), `aidd-pipelines` (grafos de execução) e `motores` (governança AST, criptografia SHA-256 e Remotion) é o caminho exato para construir sistemas AI-Driven determinísticos.
Além disso, a skill **`aidd-materialize-tutorial-stitch`** e a suíte **`tests/`** mostram um nível altíssimo de engenharia real (integração real com Playwright, Hyperframes, edge-tts, ffmpeg, testes negativos de marca e contraste).

**PORÉM**, o núcleo do Ouroboros e 80% das demais skills sofrem da **"Síndrome do Teatro Determinístico" (*Mock-Driven Architecture*)**: a documentação (`SKILL.md`, `RULES.md`, `AGENTS.md`) prega determinismo rigoroso, zero alucinação e zero *placeholders*, mas os scripts Python que deveriam executar o trabalho pesado são **cascas vazias (*stubs*)** que apenas imprimem mensagens no terminal e gravam JSONs estáticos.

---

### 2. Falhas Conceituais e de Engenharia Críticas

#### 🔴 Falha 1: A Maioria dos Scripts das Skills são "Teatro" (Hardcoded Mocks)
Embora os arquivos `RULES.md` digam *"Proibido usar TODOs ou mocks"*, veja o que os scripts realmente fazem no código atual:
* **`aidd-rea-router/scripts/rea_router.py`:** Possui um `if/else` primário que olha apenas se a string contém `youtube.com`, `.apk` ou `instagram`. **Mais grave:** Ele ignora os argumentos `--input` e `--output` passados pelo `run_pipeline.py` (usando apenas `--target` e `--goal`) e **sempre sobrescreve um arquivo fixo** no diretório do canal dark (`aidd-pipelines/canal-dark-avatar/context/input/upstream_handoff.json`). Se você rodar outro pipeline, ele corrompe o pipeline errado!
* **`aidd-rea-video-youtube/scripts/video_reengineer.py`:** Não executa `yt-dlp`, não executa `ffmpeg`, não analisa vídeo nenhum. Ele apenas lê um JSON e escreve um dicionário estático contendo `"hook_strategy": "Pattern Interrupt nos primeiros 3s"`, `"pacing_wpm": 165` e `"primary_color": "#00FF66"`, independentemente do vídeo enviado!
* **`aidd-craft-story-ptbr/scripts/dark_storycraft.py`:** Possui um texto fixo (*hardcoded*) sobre *"O segredo da engenharia reversa..."* com exatamente 42 palavras fixas. Qualquer tema ou vídeo enviado gera exatamente o mesmo roteiro.
* **`aidd-motion-remotion-core/scripts/remotion_motion.py`:** Não invoca `npx remotion render` nem compila `motores/remotion`. Ele literalmente faz `with open(remotion_video_path, "wb") as f: f.write(b"\x00" * 1024)` — **ele cria um arquivo `.mp4` corrompido com 1024 bytes nulos** quando o vídeo pré-renderizado não existe!
* **`aidd-rea-app-android`, `aidd-rea-web-saas`, `aidd-rea-social-carousel`:** Todos retornam dicionários estáticos fixos (ex: `"framework_detected": "Next.js (App Router)"`, `"slides_count": 7`) sem inspecionar o alvo real.

#### 🔴 Falha 2: Quebra de Contrato CLI entre `run_pipeline.py` e as Skills
O motor `RUN_PIPELINE_TEMPLATE.py` (usado nos pipelines) invoca todas as skills passando **exatamente** os argumentos:
`python <script.py> --input <input_path> --output <output_path>`
* **O Bug:**
  * `rea_router.py` espera `--target` e `--goal` (quebra se chamado pelo padrão do pipeline).
  * `aidd-materialize-tutorial-stitch/scripts/tutorial.py` usa subcomandos (`capture`, `compose`, `render`, `verify`, `all`) e espera `--project`, **não aceitando `--input` e `--output`**. Ou seja: a melhor skill do repositório **não consegue rodar dentro do `video-to-tutorial/run_pipeline.py`!**

#### 🔴 Falha 3: `ouroboros.py` e `run_ouroboros.py` Têm Caminhos Hardcoded para "Canal Dark"
O ponto de entrada principal (`ouroboros.py` na raiz e `aidd-ouroboros/run_ouroboros.py`) **não é universal**.
* Nas linhas 84-99 de `ouroboros.py`, após rodar o roteador, ele possui um `if target_pipeline == "canal-dark-avatar":` *hardcoded*. Se o objetivo do usuário for qualquer outra coisa (ex: criar um SaaS, analisar um APK, ou rodar `video-to-tutorial`), o `ouroboros.py` simplesmente imprime *"Pipeline será gerado pelo pipeline_creator"* e **encerra a execução sem fazer nada**!
* Além disso, na Fase 4 (`ouroboros.py`, linha 115), o código de governança está fixo para auditar apenas `aidd-pipelines/canal-dark-avatar/context/output/final_dark_video.json`.

#### 🔴 Falha 4: Os Motores de Governança Existem, Mas Estão Desconectados do Fluxo Real
Você construiu dois motores excelentes em `motores/governanca/`:
1. `handoff_crypto.py` (Assinatura e verificação SHA-256 de payloads).
2. `gate_ast.py` (Inspetor de AST que proíbe funções vazias, `except: pass` e `TODO`/`FIXME`).
3. `aidd-ouroboros/schemas/HANDOFF.schema.json` (Contrato JSON Schema Draft-07).
* **O Bug:** Nem o `run_pipeline.py` nem o `audit_runner.py` importam ou executam `handoff_crypto.py`, `gate_ast.py` ou `jsonschema.validate()`! O `audit_runner.py` faz apenas um `if "status" in data` básico. A criptografia e a validação de AST nunca são chamadas durante o pipeline.

---

### 3. Bugs Específicos de Código e Higiene de Repositório

| ID | Arquivo / Local | Descrição Exata do Bug | Severidade |
| :--- | :--- | :--- | :--- |
| **BUG-01** | `scripts/whisper_to_remotion.py` (Linhas 9-21) | **Bug de Indentação Fatal:** O bloco `with open(audio_path, "rb") as f:` abre na linha 9, mas `os.makedirs`, `with open(output_json)` e `print` estão indentados *dentro* do `with`, e não há tratamento caso `OPENAI_API_KEY` não exista no ambiente. | Alta |
| **BUG-02** | `aidd-skills/sync_all.sh` vs `sync_all.ps1` | **Dessincronização de Scripts:** `sync_all.sh` sincroniza apenas 3 skills legadas (`aidd-video-reengineer`, `aidd-skill-creator`, `aidd-session-sync` — nomes antigos sem o prefixo taxonómico!). Já `sync_all.ps1` tem 10 skills, mas **esquece** `aidd-materialize-tutorial-stitch`. | Média |
| **BUG-03** | `aidd-skills/TAXONOMY.json` | **Catálogo Desatualizado:** A skill mais completa do repositório (`aidd-materialize-tutorial-stitch`) **não está registrada** em `TAXONOMY.json`, tornando-a invisível para o roteador e para o Ouroboros. | Alta |
| **BUG-04** | `aidd-skills/*/pyproject.toml` e `requirements.txt` | **Dependências Fantasmas:** Na raiz, `requirements.txt` tem apenas `edge-tts>=6.1.9` (faltam `jsonschema`, `playwright`, `yt-dlp`, `pillow`). Nas skills, os arquivos `requirements.txt` contêm apenas comentários (`# Dependências da skill`). | Média |
| **BUG-05** | `aidd-pipelines/*/context/output/*.mp4` e `tests/smoke/renders/*.mp4` | **Poluição Binária no Git:** Dezenas de megabytes de arquivos `.mp4` e `.wav` gerados em testes estão versionados no repositório porque o `.gitignore` não bloqueia artefatos de runtime dos pipelines. | Baixa |

---

## PARTE 3: COMO CORRIGIR E ELEVAR O PROJETO (ARQUITETURA ALVO v2.0)

Para que o **OUROBOROS** cumpra a sua visão de *"criar qualquer coisa como um relógio suíço"*, precisamos fazer 4 elevações estruturais:

### 1. Padrão Universal de CLI para TODAS as Skills (Adapter Pattern)
Toda skill do ecossistema deve aceitar o contrato padrão do executor de pipelines:
```bash
python <skill_script.py> --input <caminho_handoff_entrada.json> --output <caminho_handoff_saida.json> [--workspace <dir_execucao>]
```
Se uma skill complexa como `aidd-materialize-tutorial-stitch` possui subcomandos próprios (`capture`, `compose`, `render`), criamos um **Adapter Script** (`scripts/stitch_pipeline_adapter.py`) que lê o JSON de `--input`, executa o fluxo completo e grava o JSON assinado em `--output`.

### 2. Integração Nativa de Governança no `run_pipeline.py`
O `RUN_PIPELINE_TEMPLATE.py` (e todos os `run_pipeline.py`) deve ser elevado para executar um **Triple Gate** automático a cada passo do pipeline:
1. **Gate 1 (Schema Validation):** Valida o JSON de saída contra `aidd-ouroboros/schemas/HANDOFF.schema.json`.
2. **Gate 2 (Physical Artifact Check):** Verifica se os arquivos listados em `artifacts[]` ou `payload` realmente existem no disco e possuem `size > 0`.
3. **Gate 3 (Cryptographic Seal):** Assina o handoff com `handoff_crypto.sign_handoff()` na saída da etapa `N` e verifica com `verify_handoff()` antes de iniciar a etapa `N+1`.

### 3. Motor de Descoberta e Instalação de Dependências (`dependency_resolver.py`)
Antes de rodar qualquer pipeline, o Ouroboros deve ler os arquivos `dependencies.json` de todas as skills envolvidas no `PIPELINE.json`, verificar se os binários (`ffmpeg`, `yt-dlp`, `node`, `npx`), pacotes Python e variáveis de ambiente estão presentes, e **instalar automaticamente o que faltar** (ou abortar no *Pre-Flight* com instrução exata).

### 4. Loop Autopoiético Dinâmico no `ouroboros.py`
Remover todo código *hardcoded* de `canal-dark-avatar` do `ouroboros.py`. O fluxo universal passa a ser:
1. Recebe `--goal` e `--target`.
2. Inspeciona `TAXONOMY.json` e `aidd-pipelines/`.
3. Se o pipeline necessário não existir, invoca `pipeline_creator.py` (e `skill_creator.py` para skills faltantes, validando-as com `gate_ast.py`).
4. Executa o pipeline selecionado passando um diretório isolado `workspace/<run_id>/`.
5. Executa `audit_runner.py` com verificação criptográfica e AST.

---

## PARTE 4: PLANO DE AÇÃO — NANO-TICKETS CIRÚRGICOS

Execute estes tickets sequencialmente. Cada ticket foi desenhado sob o protocolo **AIDD-Lauren**: escopo atômico, arquivos exatos, implementação determinística e **Binary Gate** de verificação.

---

### 📦 ÉPICO 1: Saneamento de Contratos, Governança e Motores Core

#### 🎫 NANO-TICKET 01: Sincronizar Taxonomia e Scripts de Sync
* **Objetivo:** Registrar todas as skills reais em `aidd-skills/TAXONOMY.json` e corrigir `sync_all.sh` / `sync_all.ps1` para descobrirem skills dinamicamente.
* **Arquivos Alvo:**
  * `aidd-skills/TAXONOMY.json`
  * `aidd-skills/sync_all.sh`
  * `aidd-skills/sync_all.ps1`
* **Ação Cirúrgica:**
  1. Adicionar `"aidd-materialize-tutorial-stitch"` na categoria `MATERIALIZE` de `aidd-skills/TAXONOMY.json`.
  2. Substituir a lista estática e defasada de `sync_all.sh` e `sync_all.ps1` por um loop dinâmico que itera sobre todos os subdiretórios `aidd-skills/aidd-*/` e executa o respectivo `sync.sh` / `sync.ps1`.
* **Binary Gate (Validação):**
  ```bash
  python -c "import json, os; tax = json.load(open('aidd-skills/TAXONOMY.json', encoding='utf-8')); skills_in_tax = [s for cat in tax['categories'].values() for s in cat['skills']]; dirs = [d for d in os.listdir('aidd-skills') if os.path.isdir(os.path.join('aidd-skills', d)) and d.startswith('aidd-')]; assert set(dirs) == set(skills_in_tax), f'Diff: {set(dirs) ^ set(skills_in_tax)}'; print('GATE PASS: Taxonomia 100% sincronizada!')"
  ```

#### 🎫 NANO-TICKET 02: Unificar Validação de Schema, Criptografia SHA-256 e AST no `audit_runner.py`
* **Objetivo:** Conectar `handoff_crypto.py`, `gate_ast.py` e `HANDOFF.schema.json` dentro de `motores/governanca/audit_runner.py`.
* **Arquivos Alvo:**
  * `motores/governanca/audit_runner.py`
  * `requirements.txt`
* **Ação Cirúrgica:**
  1. Adicionar `jsonschema>=4.20.0`, `yt-dlp`, `Pillow>=10.0.0`, `playwright` ao `requirements.txt` da raiz.
  2. Atualizar `audit_runner.py` para:
     - Validar a estrutura do JSON contra `aidd-ouroboros/schemas/HANDOFF.schema.json` (ou validar os campos obrigatórios `status`, `step`, `timestamp`).
     - Se o handoff contiver `"signature"`, validar a integridade via `handoff_crypto.verify_handoff()`.
     - Adicionar flag opcional `--check-ast <script.py>` que invoca `gate_ast.GateASTVisitor` para garantir zero *stubs* ou `TODO`s.
* **Binary Gate (Validação):**
  ```bash
  python motores/governanca/gate_ast.py motores/governanca/audit_runner.py && python motores/governanca/handoff_crypto.py
  ```

#### 🎫 NANO-TICKET 03: Elevar `RUN_PIPELINE_TEMPLATE.py` com Self-Healing, Crypto Signing e Workspace Isolado
* **Objetivo:** Tornar o executor de pipelines um motor determinístico real com assinatura SHA-256 entre etapas e verificação física de artefatos.
* **Arquivos Alvo:**
  * `aidd-skills/aidd-orchestrate-pipeline-creator/templates/RUN_PIPELINE_TEMPLATE.py`
  * `aidd-pipelines/canal-dark-avatar/run_pipeline.py`
  * `aidd-pipelines/video-to-tutorial/run_pipeline.py`
* **Ação Cirúrgica:**
  1. No `RUN_PIPELINE_TEMPLATE.py`, após cada etapa produzir seu `output_handoff`:
     - Carregar o JSON gerado, verificar se `status == "SUCCESS"`.
     - Assinar o JSON usando `handoff_crypto.sign_handoff()` e salvar de volta.
     - No início da etapa seguinte, verificar a assinatura do `input_handoff` com `verify_handoff()`.
  2. Propagar o template atualizado para os arquivos `run_pipeline.py` existentes em `aidd-pipelines/`.
* **Binary Gate (Validação):**
  ```bash
  python motores/governanca/gate_ast.py aidd-skills/aidd-orchestrate-pipeline-creator/templates/RUN_PIPELINE_TEMPLATE.py
  ```

---

### 📦 ÉPICO 2: Desacoplamento e Universalização do Kernel (`ouroboros.py`)

#### 🎫 NANO-TICKET 04: Criar o Resolvedor e Instalador de Dependências (`dependency_resolver.py`)
* **Objetivo:** Permitir que o Ouroboros verifique e instale automaticamente binários, pacotes Python/NPM e cheque variáveis de ambiente antes de rodar qualquer pipeline.
* **Arquivos Alvo:**
  * `motores/governanca/dependency_resolver.py` (Novo Arquivo)
* **Ação Cirúrgica:**
  1. Criar `dependency_resolver.py` que lê `dependencies.json` de uma skill ou pipeline:
     - Verifica binários de sistema com `shutil.which()` (ex: `ffmpeg`, `ffprobe`, `node`, `npx`).
     - Verifica pacotes Python com `importlib.metadata` e oferece flag `--auto-install` (`pip install`).
     - Retorna um relatório JSON determinístico de `READY` ou `MISSING_DEPENDENCIES`.
* **Binary Gate (Validação):**
  ```bash
  python motores/governanca/dependency_resolver.py --check aidd-ouroboros/dependencies.json
  ```

#### 🎫 NANO-TICKET 05: Refatorar `rea_router.py` e `ouroboros.py` para Roteamento Dinâmico Universal
* **Objetivo:** Remover o caminho fixo (`hardcoded`) de `canal-dark-avatar` de dentro de `rea_router.py` e `ouroboros.py`.
* **Arquivos Alvo:**
  * `aidd-skills/aidd-rea-router/scripts/rea_router.py`
  * `ouroboros.py`
  * `aidd-ouroboros/run_ouroboros.py`
* **Ação Cirúrgica:**
  1. Em `rea_router.py`: adicionar suporte a `--input` e `--output` (além de `--target` e `--goal`). Se `--output` não for passado, salvar no pipeline correspondente ao `target_pipeline` detectado (`aidd-pipelines/<target_pipeline>/context/input/upstream_handoff.json`), e **nunca** fixo em `canal-dark-avatar`.
  2. Adicionar heurística em `rea_router.py` para detectar pedidos de tutorial (`tutorial`, `passo a passo`, `stitch`, `manual`) e rotear para `video-to-tutorial`.
  3. Em `ouroboros.py`: substituir o `if target_pipeline == "canal-dark-avatar":` por uma busca dinâmica em `aidd-pipelines/<target_pipeline>/PIPELINE.json`. Se o pipeline existir, executá-lo; se não existir, invocar `pipeline_creator.py` para criá-lo dinamicamente e depois executá-lo.
* **Binary Gate (Validação):**
  ```bash
  python motores/governanca/gate_ast.py ouroboros.py && python motores/governanca/gate_ast.py aidd-skills/aidd-rea-router/scripts/rea_router.py
  ```

---

### 📦 ÉPICO 3: Erradicação de Stubs (Transformar Mocks em Engenharia Real)

#### 🎫 NANO-TICKET 06: Criar Adapter de Pipeline para `aidd-materialize-tutorial-stitch`
* **Objetivo:** Conectar a skill `aidd-materialize-tutorial-stitch` ao contrato `--input` / `--output` do pipeline `video-to-tutorial`.
* **Arquivos Alvo:**
  * `aidd-skills/aidd-materialize-tutorial-stitch/scripts/stitch_adapter.py` (Novo Arquivo)
  * `aidd-pipelines/video-to-tutorial/PIPELINE.json`
* **Ação Cirúrgica:**
  1. Criar `stitch_adapter.py` que recebe `--input <handoff.json>` e `--output <out.json>`, extrai os parâmetros do projeto, chama `tutorial.py verify` / `compose` / `render` conforme configurado no payload, e grava o handoff final compatível com o `audit_runner.py`.
  2. Atualizar a Etapa 3 de `aidd-pipelines/video-to-tutorial/PIPELINE.json` para apontar para `stitch_adapter.py`.
* **Binary Gate (Validação):**
  ```bash
  python motores/governanca/gate_ast.py aidd-skills/aidd-materialize-tutorial-stitch/scripts/stitch_adapter.py
  ```

#### 🎫 NANO-TICKET 07: Implementar Extração Real em `video_reengineer.py` (`ffprobe` / `yt-dlp`)
* **Objetivo:** Substituir o JSON estático de `aidd-rea-video-youtube/scripts/video_reengineer.py` por extração real de metadados de vídeo/URL.
* **Arquivos Alvo:**
  * `aidd-skills/aidd-rea-video-youtube/scripts/video_reengineer.py`
* **Ação Cirúrgica:**
  1. Se o `target` for um arquivo de vídeo local (`.mp4`, `.mkv`, `.mov`), executar `ffprobe -v quiet -print_format json -show_format -show_streams` para extrair duração real, FPS, resolução (`width`x`height`), codec de áudio e vídeo.
  2. Se o `target` for uma URL do YouTube e `yt-dlp` estiver disponível, rodar `yt-dlp --dump-json --no-download <url>` para extrair título, duração, capítulos, resolução e legendas automáticas.
  3. Usar fallback gracioso documentado no JSON (`"extraction_mode": "EMPIRICAL_FFPROBE" | "EMPIRICAL_YTDLP" | "HEURISTIC_FALLBACK"`) sem mentir sobre os dados extraídos.
* **Binary Gate (Validação):**
  ```bash
  python aidd-skills/aidd-rea-video-youtube/scripts/video_reengineer.py --input tests/smoke/renders/smoke.mp4 --output tests/smoke/test_rea_out.json && python -c "import json, os; d=json.load(open('tests/smoke/test_rea_out.json')); assert d['status']=='SUCCESS'; os.remove('tests/smoke/test_rea_out.json'); print('GATE PASS!')"
  ```

#### 🎫 NANO-TICKET 08: Corrigir Bug de Indentação em `whisper_to_remotion.py` e Eliminar Bytes Nulos em `remotion_motion.py`
* **Objetivo:** Corrigir o bug sintático/lógico de `scripts/whisper_to_remotion.py` e proibir `remotion_motion.py` de gerar arquivos `.mp4` falsos com bytes nulos (`\x00`).
* **Arquivos Alvo:**
  * `scripts/whisper_to_remotion.py`
  * `aidd-skills/aidd-motion-remotion-core/scripts/remotion_motion.py`
* **Ação Cirúrgica:**
  1. Em `scripts/whisper_to_remotion.py`: fechar corretamente o bloco `with open(audio_path, "rb") as f:` na chamada da API, adicionar verificação de `OPENAI_API_KEY` e suporte a fallback determinístico local (lendo `.words.json` já gerados pelo `edge-tts`).
  2. Em `remotion_motion.py`: remover `f.write(b"\x00" * 1024)`. Se o vídeo não existir, acionar `npx remotion render` em `motores/remotion` ou gerar um vídeo válido real via `ffmpeg -f lavfi -i color=c=#0a0a0f:s=1080x1920:d=5` com filtro de texto/waveform, garantindo que todo `.mp4` gerado seja um container de vídeo H.264 íntegro e reproduzível.
* **Binary Gate (Validação):**
  ```bash
  python motores/governanca/gate_ast.py scripts/whisper_to_remotion.py && python motores/governanca/gate_ast.py aidd-skills/aidd-motion-remotion-core/scripts/remotion_motion.py
  ```

#### 🎫 NANO-TICKET 09: Implementar Inspeção Empírica Real nas Skills REA (`web-saas`, `app-android`, `social-carousel`)
* **Objetivo:** Remover os *stubs* fixos das 3 skills de engenharia reversa restantes.
* **Arquivos Alvo:**
  * `aidd-skills/aidd-rea-web-saas/scripts/web_reengineer.py`
  * `aidd-skills/aidd-rea-app-android/scripts/app_reengineer.py`
  * `aidd-skills/aidd-rea-social-carousel/scripts/social_reengineer.py`
* **Ação Cirúrgica:**
  1. `web_reengineer.py`: Fazer requisição HTTP real (`urllib.request`) ou inspecionar arquivo HTML local, extraindo tags `<title>`, `<meta>`, links de folhas de estilo, variáveis CSS (`--*`), fontes e detectando o framework real pelas assinaturas no DOM (`_next`, `astro`, `vite`, `react`).
  2. `app_reengineer.py`: Se o alvo for um arquivo `.apk` ou `.zip` real existente no disco, abrir com `zipfile.ZipFile` (biblioteca padrão), listar `AndroidManifest.xml`, `classes.dex`, `lib/` (arquiteturas nativas) e `assets/` reais.
  3. `social_reengineer.py`: Se o alvo for uma imagem ou pasta de imagens local, usar `PIL.Image` (já listado no `requirements.txt` da skill) para extrair dimensões reais (`width`, `height`), proporção (`aspect_ratio`) e paleta de cores dominante via quantização real da imagem.
* **Binary Gate (Validação):**
  ```bash
  python motores/governanca/gate_ast.py aidd-skills/aidd-rea-web-saas/scripts/web_reengineer.py && python motores/governanca/gate_ast.py aidd-skills/aidd-rea-app-android/scripts/app_reengineer.py && python motores/governanca/gate_ast.py aidd-skills/aidd-rea-social-carousel/scripts/social_reengineer.py
  ```

#### 🎫 NANO-TICKET 10: Higiene de Repositório e `.gitignore` Determinístico
* **Objetivo:** Impedir que artefatos transitórios de execução (`state.json`, `context/handoffs/*.json`, `context/output/*.mp4`) sujem o status do Git após rodar o Ouroboros.
* **Arquivos Alvo:**
  * `.gitignore`
* **Ação Cirúrgica:**
  1. Adicionar regras no `.gitignore` para ignorar diretórios de saída temporários (`workspace/`, `aidd-pipelines/*/context/handoffs/*.json`, `aidd-pipelines/*/context/output/*`, `aidd-pipelines/*/state.json`), mantendo apenas arquivos `.gitkeep` ou fixtures explícitas de teste.
* **Binary Gate (Validação):**
  ```bash
  python ouroboros.py --target "https://youtube.com/watch?v=test" --goal "Criar video dark" && git status --short
  ```