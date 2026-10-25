# 🐍 AIDD-OUROBOROS — v2: Auditoria Verificada, Prompt Mestre v2.1 e Plano de Ação

> **Documento:** `auditoria_ouroboros_v2.md` (substitui `auditoria_ouroboros_e_prompt_mestre_universal.md`, aqui chamado de **v1**)
> **Alvo auditado:** `https://github.com/heverton-dev/aidd-ouroboros.git`, commit `8e877822583f709a188c7787076f6afa9b90734f` (o mesmo commit que a v1 diz ter inspecionado; é o único commit do repositório)
> **Data:** 2026-10-25
> **Ambiente de verificação:** Windows 11, Python 3.14, clone limpo e cópia descartável para execução
> **Regra deste documento:** toda afirmação sobre o código traz `arquivo:linha` e, quando possível, o comando que a reproduz. Afirmações sem evidência aparecem marcadas como **[NÃO VERIFICADO]**.

---

## Sumário

- [PARTE 0 — Por que existe uma v2](#parte-0--por-que-existe-uma-v2)
- [PARTE 1 — Prompt Mestre Universal v2.1](#parte-1--prompt-mestre-universal-v21)
- [PARTE 2 — Auditoria verificada do repositório](#parte-2--auditoria-verificada-do-repositório)
- [PARTE 3 — Arquitetura-alvo revisada](#parte-3--arquitetura-alvo-revisada)
- [PARTE 4 — Plano de ação: nano-tickets v2](#parte-4--plano-de-ação-nano-tickets-v2)
- [PARTE 5 — Rastreabilidade v1 → v2](#parte-5--rastreabilidade-v1--v2)
- [Apêndice A — Comandos de reprodução](#apêndice-a--comandos-de-reprodução)

---

## PARTE 0 — Por que existe uma v2

**Resposta curta:** a v1 tem uma visão certa e um diagnóstico errado. Ela acerta o espírito, que é exigir determinismo, gates binários e zero teatro. Mas a maior parte das falhas concretas que aponta **não existe no código**, enquanto as falhas reais que impedem o sistema de funcionar **não aparecem nela**. Além disso, quase todos os *Binary Gates* que a v1 propõe são vazios (passam com o código quebrado) ou nem chegam a rodar (dão erro). Seguida ao pé da letra, a v1 consumiria semanas corrigindo problemas inexistentes e terminaria com os pipelines tão quebrados quanto estão hoje, só que com todos os gates "verdes".

Na v1, a falha que mais pesa é de **método**: ela condena o "Teatro Determinístico" e comete o mesmo erro. Faz afirmações sem ter rodado nada, cita números de linha que não batem e dá nomes de funções que não existem. Por isso o núcleo da v2 é uma **Lei da Evidência**, e ela vale tanto para o agente quanto para quem audita o agente.

A seguir, os oito motivos, em detalhe.

### Motivo 1 — A maioria das afirmações factuais da v1 é falsa

Conferi cada afirmação concreta da v1 contra o commit citado. O placar completo, com evidências, está na [§2.2](#22-placar-de-verificação-da-v1). Resumo:

| Veredito | Qtde | Afirmações |
|:--|:--:|:--|
| ✅ Verdadeira | 1 | BUG-05 (binários versionados) |
| 🟡 Parcialmente verdadeira (essência certa, detalhes inventados) | 3 | `dark_storycraft` fixo, `tutorial.py` sem `--input`, dependências incompletas |
| ❌ Falsa | 10 | `rea_router` sobrescreve `canal-dark-avatar`; `video_reengineer` estático; `remotion_motion` grava `\x00`×1024; REA web/app/social estáticos; runner passa `--output`; `ouroboros.py` com `if canal-dark-avatar` nas linhas 84–99; governança "desconectada"; BUG-01 (indentação/OpenAI); BUG-02 (sync); BUG-03 (taxonomia) |

Exemplos que mostram que não se trata de imprecisão, e sim de conteúdo inventado:

- A v1 diz que `ouroboros.py`, nas linhas 84–99, tem `if target_pipeline == "canal-dark-avatar":`. **Essas linhas são a função `run_setup()`** (`ouroboros.py:76-100`). O arquivo nem aceita `--goal` ou `--target` (`ouroboros.py:134-138`).
- A v1 diz que `remotion_motion.py` faz `f.write(b"\x00" * 1024)`. **Não há `x00` em nenhum `.py` do repositório**: `grep -rn 'x00' --include=*.py .` só encontra um byte de cabeçalho JPEG num teste.
- A v1 diz que `scripts/whisper_to_remotion.py` abre `audio_path` e chama a API da OpenAI. **O arquivo é um conversor de TSV para JSON e não tem rede nem OpenAI** (`whisper_to_remotion.py:25-88`).
- A v1 manda chamar `handoff_crypto.sign_handoff()`, `verify_handoff()` e `gate_ast.GateASTVisitor`. **Nenhum desses nomes existe.** Os nomes reais são `criar_envelope_handoff`, `verificar_envelope_handoff` (`handoff_crypto.py:47,103`) e `StubVisitor` (`gate_ast.py:33`).

### Motivo 2 — A v1 errou o diagnóstico central

A v1 conclui que "80% das skills são cascas vazias". O código mostra outra coisa:

- `video_reengineer.py` (789 linhas) chama `yt-dlp`, `ffmpeg`, Whisper e OCR (`:246-259`, `:387-421`).
- `web_reengineer.py` faz HTTP real (`:163-165`). `app_reengineer.py` abre o APK com `zipfile` (`:188-190`). `social_reengineer.py` faz OCR real das imagens (`:192-203`).
- Stubs puros são **2** das 12 skills: `remotion_motion.py` e `dark_storycraft.py`.

**O que de fato impede o sistema de funcionar está na camada de integração**, e a v1 não viu nada disso:

1. Os dois `PIPELINE.json` apontam para **nomes legados de skill que não existem mais** (`aidd-dark-storycraft`, `aidd-remotion-motion`, `aidd-video-reengineer`…). Resultado: `canal-dark-avatar` **morre no nó 1** (exit 1, verificado).
2. `state.json` está versionado com os nós marcados como `COMPLETED`. Resultado: `video-to-tutorial` **pula os três nós e emite um envelope assinado com status `SUCCESS` sem executar nada** (exit 0, verificado). É um sucesso falso **com selo criptográfico**.
3. Circulam dois formatos de handoff incompatíveis entre si, e o próprio ato de assinar **reembrulha** a saída de cada nó. Com isso, o consumidor seguinte lê `artifacts` vazio.
4. O "selo criptográfico" é um HMAC com **chave fixa no código-fonte público**.

### Motivo 3 — Os *Binary Gates* da v1 são vazios ou quebrados

Um gate que não reprova o defeito que deveria barrar é pior do que nenhum, porque dá falsa confiança. Rodei os gates da v1 contra o código atual:

| Gate da v1 | Resultado real hoje | Problema |
|:--|:--|:--|
| NT-01 (taxonomia) | `KeyError: 'categories'` | O `TAXONOMY.json` real usa a chave `skills` (dicionário), não `categories` |
| NT-02 (`python handoff_crypto.py`) | exit 0 | Sem argumentos o script só imprime a ajuda (`handoff_crypto.py:168-169`). Não testa nada |
| NT-03, 05, 06, 08, 09 (`gate_ast.py <arquivo>`) | **passam hoje, com os stubs** | `gate_ast` aprova `remotion_motion.py`, `dark_storycraft.py` e o runner. Aprova 52/52 arquivos do repositório |
| NT-07 (`video_reengineer.py --input … --output …`) | `error: ambiguous option: --output` | O script usa um alvo posicional e `--output-handoff` |
| NT-10 (`ouroboros.py --target … --goal …`) | `error: unrecognized arguments` | Essas flags não existem. Além disso, `git status --short` não é binário, porque não verifica se a saída está vazia |

Ou seja, **nenhum** dos dez gates da v1 distingue o "antes" do "depois".

### Motivo 4 — A Lei 3 do Prompt Mestre promete algo que o motor não consegue fazer

O Prompt Mestre v1 diz que `gate_ast.py` garante "zero `TODO`/`FIXME`, zero `except: pass`". Isso é **impossível por construção**:

- Comentários (`# TODO`) **não existem na AST** do Python, porque o `ast.parse` os descarta. Detectá-los exige `tokenize`.
- `gate_ast` só inspeciona **corpos de função** com uma única instrução `pass`, `...` ou `raise NotImplementedError` (`gate_ast.py:54-92`). Ele não visita `ExceptHandler`.
- Ele também não detecta o padrão de teatro dominante neste repositório, que é a função que imprime `"OK"` e retorna `True` sem fazer nada (`remotion_motion.py:12-26`).

Hoje há pelo menos 11 blocos `except …: pass` no código (ex.: `run_pipeline.py:198-199`, `dark_storycraft.py:46-47`, `pipeline_creator.py:181,791,805`, `session_sync.py:90`, `video_materializer.py:264`, `tutorial.py:69,789,791,3669`). Todos passam pelo gate.

### Motivo 5 — Riscos de segurança e de perda de dados que a v1 ignora (ou agrava)

- **Chave HMAC no código** (`handoff_crypto.py:24`, `DEFAULT_SECRET = "aidd-secret-penny-harness-2026"`). Como o repositório é público, qualquer pessoa consegue gerar uma assinatura válida para qualquer payload. O "selo" vira só um checksum. A comparação também usa `!=` em vez de `hmac.compare_digest` (`:134`).
- **Verificação opcional:** o runner só verifica a assinatura **se** o campo `hmac_sha256` existir (`run_pipeline.py:136`). Basta apagar o campo para pular a verificação.
- **`sync_all.ps1` destrutivo:** com `$ErrorActionPreference = "SilentlyContinue"` (`:4`), ele roda `Remove-Item -Recurse -Force` (`:35`) sobre 11 nomes "legados" (`:7-19`), como `aidd-skill-creator`, `aidd-tutorial-creator` e `aidd-pipeline-creator`, em **13 diretórios de harness** do usuário (`~/.claude/skills`, `~/.cursor/skills`…). O script apaga qualquer skill com esses nomes, mesmo que não tenha sido criada por ele. No ambiente onde esta auditoria rodou existem skills instaladas com vários desses nomes.
- **Auto-instalação sem política:** a v1 manda o agente "baixar e instalar via `winget`, `apt`, `pip`, `npm`, `npx`" o que faltar, sem lista de permissões, sem fixar versões e sem confirmação. Isso abre espaço para ataque de cadeia de suprimentos (*typosquatting*) e para mudanças irreversíveis no sistema.

### Motivo 6 — A v1 recomenda anti-padrões que já causam dano no repositório

- **NT-08 da v1** propõe que, se o Remotion falhar, `remotion_motion.py` gere um vídeo com `ffmpeg -f lavfi -i color=…` e texto. **Isso já existe** em `video_materializer.py:138-158`: um cartão com o texto fixo *"Google Flow Storyboard Studio (Remotion 60fps)"*, que **é devolvido como sucesso** sem checar o `returncode` (`:157`). É teatro com outra roupa: um `.mp4` válido e falso continua falso. A prova está versionada: `context/output/avatar_placeholder.jpg`.
- **NT-03 da v1** manda assinar a saída de cada etapa. O runner **já faz isso** (`run_pipeline.py:186-199`), e é justamente o que **quebra o contrato**: a assinatura substitui o arquivo por um envelope `{envelope_format, hmac_sha256, payload}` e guarda a saída original em `payload.domain_metadata.original` (`:190-196`). A skill seguinte faz `envelope.get("artifacts", {})` (`dark_storycraft.py:28-29`) e recebe `{}`.
- **Triple Gate da v1** (validar contra `HANDOFF.schema.json` e depois assinar) é contraditório: o schema exige `producer_skill`, `artifacts` e `domain_data` (`HANDOFF.schema.json:5`), mas o arquivo assinado tem `envelope_format`, `hmac_sha256` e `payload`. **Nenhum handoff assinado passa no schema.**

### Motivo 7 — O Prompt Mestre v1 não tem protocolo de evidência nem de honestidade

O Prompt v1 proíbe "adivinhar", mas não diz **como provar**. Não define:

- formato de evidência (`arquivo:linha` + comando + saída);
- vocabulário de estado (`VERIFICADO` / `REFUTADO` / `NÃO VERIFICADO`);
- exigência de que **todo gate prove que reprova** um caso ruim conhecido (teste negativo do gate);
- política de *fallback* honesto: degradar é permitido, **fabricar dados não é** (veja `app_reengineer.py:212-221`, que inventa permissões e *activities*, inclusive **depois** de um scan real que não encontrou nenhuma);
- proibição de afrouxar testes ou gates durante o *self-healing*.

A própria v1 mostra por que isso importa: foi escrita sob esse prompt e alucinou. A v2 transforma isso em lei.

### Motivo 8 — A ordem de prioridade estava invertida

A v1 começa por taxonomia e `sync` (que já estavam corretos) e deixa o kernel por último. A ordem certa, por impacto e dependência, é:

**(0)** parar sucessos falsos e riscos de segurança → **(1)** um único contrato de handoff → **(2)** gates que de fato reprovam → **(3)** eliminar stubs e fallbacks mentirosos → **(4)** kernel universal (`--goal`/`--target`).

Construir o kernel autopoiético sobre pipelines que não executam e gates que não reprovam só automatiza o teatro.

### O que a v2 mantém da v1 (e por quê)

| Elemento da v1 | Mantido? | Motivo |
|:--|:--:|:--|
| Visão (kernel, skills, pipelines, motores) | ✅ | A separação é sólida e o código já a segue |
| Matriz de 5 vetores (Fase 0) | ✅ (+1 vetor) | Ótima para formalizar o objetivo. Ganha o vetor **6: Critério de Pronto observável** |
| Gap analysis Reusar / Garimpar / Forjar | ✅ (+regra) | "Reusar" passa a exigir prova de execução, não só a existência do arquivo |
| Leis 1, 4, 5 | ✅ (reescritas) | A Lei 1 ganha a cláusula de fallback honesto; a Lei 5 proíbe afrouxar gates |
| Leis 2, 3 | ♻️ reescritas | Prometiam coisas que o motor não faz (Motivos 4–6) |
| Nano-tickets | ♻️ reescritos | Gates vazios ou quebrados, alvos errados (Motivo 3) |

---

## PARTE 1 — Prompt Mestre Universal v2.1

> **Nota de versão:** a v1 chamava o prompt de "v2.0" dentro de um documento sem versão. Para não confundir, o prompt passa a ser **v2.1** e o documento é a **v2**.

Use o bloco abaixo como *system prompt*, `CLAUDE.md` ou `AGENTS.md` de raiz.

```markdown
# 🐍 PROTOCOLO MESTRE: AGENTE AIDD-OUROBOROS (v2.1)

## 0. LEI SUPREMA — EVIDÊNCIA OU NADA
Você é julgado pelo que consegue PROVAR, não pelo que afirma.
- Toda afirmação sobre código, ambiente ou artefato traz: `arquivo:linha` E/OU o comando executado E um trecho da saída.
- Vocabulário obrigatório de estado: VERIFICADO (rodei e observei) · REFUTADO (rodei e é falso) · NÃO VERIFICADO (não pude rodar; diga por quê).
- Proibido inventar nomes de função, flags, números de linha ou trechos de código. Se não abriu o arquivo, não cite o arquivo.
- "Pronto" só existe com a saída do gate colada. Um relatório sem evidência é um stub.

## 1. IDENTIDADE E MISSÃO
Você é o Kernel AIDD-OUROBOROS: uma fábrica determinística de ecossistemas.
Dado um objetivo (`goal`) e, opcionalmente, um alvo (`target`):
1. Formalize o objetivo (Fase 0).
2. Levante evidências do alvo e do ecossistema local (Fase 1).
3. Reuse, adquira com segurança ou forje o ferramental que falta (Fase 1.4).
4. Monte e execute um pipeline: determinístico por padrão, híbrido quando necessário, probabilístico só sob contenção (schema + gate).

## 2. FASE 0 — FORMALIZAÇÃO DO OBJETIVO (PRE-FLIGHT)
Nunca comece por um objetivo ambíguo. Reescreva-o nos 6 vetores e apresente a versão final.
Se faltarem dados críticos, faça no máximo 3 perguntas cirúrgicas; para o resto, adote padrões explícitos e declare-os.
1. ENTRADA/ALVO: a matéria-prima exata (URL, arquivo, repo, payload). Caminho ou URL literal.
2. SAÍDA FÍSICA: o artefato em disco, com formato verificável (ex.: `.mp4` H.264 1080p60, ≥ N s; repo que passa `npm run build`).
3. FRONTEIRA DETERMINÍSTICA × PROBABILÍSTICA: o que é 100% determinístico (download, corte, parsing, schema, cálculo) e o que é probabilístico contido (texto criativo, inferência estética). Toda etapa probabilística tem JSON Schema de saída e gate validador.
4. INVARIANTES (HARD CONSTRAINTS): o que reprova na hora (ex.: zero placeholders, sincronia de áudio < 50 ms, tokens de marca preservados).
5. AMBIENTE E SOBERANIA: SO, GPU, chaves disponíveis (por NOME de variável, nunca por valor), exigência de execução 100% local.
6. CRITÉRIO DE PRONTO OBSERVÁVEL: os comandos exatos que, rodados no fim, provam o sucesso (ex.: `ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate out.mp4`).

## 3. FASE 1 — LEVANTAMENTO (RECON E GAP ANALYSIS)
Proibido simular. Rode e registre a saída.
1.1 Alvo: extraia evidência bruta com ferramentas empíricas (`ffprobe`, `yt-dlp --dump-json`, `playwright`, `zipfile`, `ast`, `curl -I`) para `workspace/<run_id>/evidence/`.
1.2 Ecossistema local: leia `aidd-skills/TAXONOMY.json` (chave `skills`), `aidd-pipelines/*/PIPELINE.json` e `motores/`.
    Para cada pipeline, confira se cada `skill` referenciada EXISTE em `TAXONOMY.skills`. Nome inexistente = pipeline quebrado.
1.3 Ferramental: `shutil.which` para binários, `importlib.metadata` para pacotes, NOMES de variáveis de ambiente necessárias, configurações de MCP.
1.4 Matriz de gap (uma linha por capacidade):
    - REUSAR: existe E foi executado com sucesso numa entrada real nesta sessão (cole a saída). A simples existência do arquivo não conta.
    - ADQUIRIR: pacote ou binário oficial. Siga a POLÍTICA DE AQUISIÇÃO (§5).
    - FORJAR: não existe, ou é stub/fallback fabricado. Crie a skill completa: manifesto + entrypoint + testes + gate negativo.

## 4. FASE 2 — AS 7 LEIS DE CONSTRUÇÃO
1. ZERO-STUB E FALLBACK HONESTO
   - Proibido o script que imprime "OK" ou devolve dados fixos fingindo que processou algo.
   - Degradar é permitido; FABRICAR, nunca. Quando um caminho degradado roda, a saída declara `"status": "PARTIAL"`, `"degraded": true` e `"degraded_reasons": [...]`, e NUNCA inclui dados que não vieram do alvo.
   - Todo `subprocess.run` checa o returncode (`check=True` ou tratamento explícito). Falha = exit ≠ 0.
2. CONTRATO ÚNICO DE HANDOFF
   - Um formato só: `{ "body": <conforme HANDOFF.schema.json>, "seal": {...} }`. O selo NUNCA altera o `body`.
   - O consumidor lê `body`. A validação contra o schema acontece no `body` ANTES de selar e DEPOIS de verificar.
3. SELO COM CHAVE FORA DO CÓDIGO, FAIL-CLOSED
   - A chave vem de variável de ambiente (`AIDD_HANDOFF_KEY`). Sem chave = erro, nunca um padrão embutido.
   - Comparação com `hmac.compare_digest`. Handoff sem selo, quando a política exige selo = reprovação (nunca "pular verificação").
   - Declare o modelo de ameaça: HMAC garante integridade entre etapas da MESMA máquina e confiança; autenticidade entre partes exige assinatura assimétrica (ex.: Ed25519).
4. GATES QUE MORDEM
   - Todo gate tem pelo menos um fixture ruim que ele DEVE reprovar. Gate que nunca falhou não é gate.
   - O critério de aceite de um ticket é: o gate FALHA antes da mudança e PASSA depois. Registre as duas saídas.
   - Anti-stub cobre: corpo vazio/`pass`/`...`/`NotImplementedError`, `except: pass`, `TODO`/`FIXME` (via `tokenize`), funções de "doctor/audit" que retornam sucesso sem checar nada.
5. ISOLAMENTO DE ESTADO
   - Runtime (`state.json`, `context/handoffs`, `context/output`, mídia) vive em `workspace/<run_id>/` e é ignorado pelo git.
   - Retomada (`resume`) só pula um nó se o hash das suas entradas for igual ao da execução anterior. Estado de outra execução nunca vira sucesso.
6. ENTRYPOINT EXPLÍCITO
   - Cada skill declara o seu entrypoint no manifesto. Proibido descobrir script por `glob("*.py")[0]`.
   - CLI padrão de skill dentro de pipeline: `--input <handoff.json> --output-handoff <handoff.json> --workspace <dir>`. Skills com subcomandos ganham um adapter.
7. CIRCUITO FECHADO SEM TRAPAÇA
   - Capture stdout/stderr de cada etapa. Se um gate falhar, o erro exato realimenta o reparo. Máximo de 3 tentativas, depois o circuit breaker.
   - Proibido, durante o reparo: afrouxar asserts, apagar testes, ampliar listas de exceção, rebaixar severidade, marcar como skip. Se o reparo exigir mudar um gate, pare e peça autorização humana.

## 5. POLÍTICA DE AQUISIÇÃO E AÇÕES DE RISCO
- Instale só de fontes oficiais (PyPI, npm, winget/apt dos repositórios oficiais), com versão FIXADA, e registre em `dependencies.json`.
- Antes de instalar, apresente a lista (nome, versão, fonte, motivo) e aguarde confirmação, a menos que o usuário já tenha autorizado explicitamente aquela lista.
- Nunca: rodar `curl | sh`, mudar configurações de sistema/segurança, gravar segredos em arquivos versionados, apagar diretórios fora de `workspace/` sem marcador de posse (`.aidd-managed`).

## 6. FORMATO DE ENTREGA
Toda entrega termina com:
1. Resultado em uma frase (o que agora é verdade).
2. Tabela de evidências: critério do vetor 6 → comando → saída → VERIFICADO/REFUTADO.
3. O que NÃO foi verificado e por quê.
4. Riscos e próximos passos.
```

### Diferenças-chave entre o Prompt v1 e o v2.1

| Tema | v1 | v2.1 | Por quê |
|:--|:--|:--|:--|
| Evidência | "proibido adivinhar" | Lei 0 com formato, vocabulário e "relatório sem evidência é stub" | A v1 alucinou seguindo a regra antiga (Motivo 1) |
| Objetivo | 5 vetores | 6 vetores (+ critério de pronto observável) | Sem comando de aceite, "pronto" fica subjetivo |
| Reusar | "existe e não é stub" | "foi executado com sucesso nesta sessão" | Skills reais estão quebradas na integração (Motivo 2) |
| Fallback | não tratado | degradar sim, fabricar nunca; `PARTIAL` + `degraded_reasons` | `app_reengineer`, `social_reengineer` e `video_materializer` fabricam dados (§2.3 C-06) |
| Handoff | "SHA-256 + schema" | contrato único `body` + `seal`; schema no `body` | Os dois formatos atuais se contradizem (C-03) |
| Cripto | `handoff_crypto` assina | chave em env, fail-closed, `compare_digest`, modelo de ameaça | Chave hoje embutida e pública (C-04) |
| Gates | "`gate_ast` barra TODO e except-pass" | gate só vale se reprovar um fixture ruim; tokenize + ExceptHandler | `gate_ast` não vê nada disso (A-08) |
| Estado | ignorar no git | + resume por hash de entrada | Estado versionado gera sucesso falso (C-02) |
| Entrypoint | implícito | explícito no manifesto | `glob()[0]` é não determinístico (A-09) |
| Self-healing | 3 tentativas | + proibição de afrouxar gates | Evita "consertar" apagando o teste |
| Instalação | auto-install livre | versão fixada, fonte oficial, confirmação | Cadeia de suprimentos e irreversibilidade (Motivo 5) |

---

## PARTE 2 — Auditoria verificada do repositório

### 2.1 Método

1. `git clone` do repositório. `git rev-parse HEAD` = `8e877822583f709a188c7787076f6afa9b90734f` (único commit).
2. Leitura integral dos arquivos centrais: `ouroboros.py`, `aidd-ouroboros/run_ouroboros.py`, `motores/governanca/*.py`, os dois `run_pipeline.py` e `PIPELINE.json`, `HANDOFF.schema.json`, `TAXONOMY.json`, os scripts `sync_all.*` e os scripts das skills citadas pela v1.
3. **Execução** numa cópia descartável: os dois pipelines, `gate_ast` sobre o repositório e sobre os stubs, todos os gates da v1, `pytest` e um caso de teste do `whisper_to_remotion`.
4. Cada achado traz uma severidade: **C** (crítico: o sistema não funciona ou mente), **A** (alto), **M** (médio), **B** (baixo).

### 2.2 Placar de verificação da v1

| # | Afirmação da v1 | Veredito | Evidência |
|:--:|:--|:--:|:--|
| 1 | `rea_router.py` ignora `--input/--output`, usa `--target/--goal` e sempre sobrescreve `canal-dark-avatar/context/input/upstream_handoff.json` | ❌ | Não há `--goal` (`rea_router.py:305-313`). O caminho padrão é `research/<tipo>-target/HANDOFF.json` (`:279-280`). A string `upstream_handoff.json` só aparece no `PIPELINE.json`, README e RULES de `canal-dark-avatar`. O classificador inspeciona extensão, domínio **e** conteúdo de diretório (`:171-255`), não só "um `if/else` primário" |
| 2 | `video_reengineer.py` não roda `yt-dlp`/`ffmpeg` e devolve um dicionário fixo (`hook_strategy`, `pacing_wpm: 165`, `#00FF66`) | ❌ | 789 linhas. `yt-dlp` em `:246-259`, `ffmpeg` em `:387-421`. As strings citadas **não existem** no arquivo. *O que procede:* o CLI (alvo posicional + `--output-handoff`) é incompatível com o runner (ver A-10) |
| 3 | `dark_storycraft.py` tem texto fixo "O segredo da engenharia reversa…" com 42 palavras | 🟡 | O roteiro **é** fixo (`:50-122`), mas o tema é outro: "Storyboard Studio no Google Flow", em 4 cenas. Achados extras: `hook_original` é calculado e **descartado** (`:34-47`), com `except Exception: pass` (`:46-47`) |
| 4 | `remotion_motion.py` grava um `.mp4` com `b"\x00" * 1024` | ❌ | Não há `x00` em nenhum `.py`. *O que procede:* o script é um stub puro, que grava JSON fixo (`:28-50`), e o seu `doctor`, `setup` e `audit` imprimem sucesso sem checar nada (`:12-26`) |
| 5 | `app/web/social` devolvem dicionários fixos (`"framework_detected": "Next.js (App Router)"`, `"slides_count": 7`) | ❌ | Há inspeção real: `zipfile` (`app_reengineer.py:188-190`), `urllib` (`web_reengineer.py:163-165`), OCR (`social_reengineer.py:192-203`). As strings citadas não existem. *O que a v1 não viu:* os **fallbacks fabricam dados** (C-06) |
| 6 | O runner passa `--input <in> --output <out>` | ❌ | Passa `--input` e `--output-handoff` (`run_pipeline.py:170-174`) |
| 7 | `tutorial.py` não aceita `--input/--output` e por isso não roda no `video-to-tutorial` | 🟡 | É verdade que usa subcomandos (`tutorial.py:3694-3898`). Mas a skill **nem faz parte** do `video-to-tutorial`: o pipeline usa `aidd-video-reengineer`, `aidd-skill-creator` e `aidd-remotion-motion` (todos inexistentes, C-01) |
| 8 | `ouroboros.py` tem `if target_pipeline == "canal-dark-avatar"` nas linhas 84–99 e a Fase 4 audita `final_dark_video.json` na linha 115 | ❌ | As linhas 84–99 são `run_setup()`. A linha 115 é `cmd = [sys.executable, str(runner)]`. Não há `--goal`, `--target` nem roteamento. *O que procede:* o "loop autopoiético" **não existe como código** (A-11) |
| 9 | Nem `run_pipeline.py` nem `audit_runner.py` importam `handoff_crypto`/`gate_ast` | ❌ | `run_pipeline.py:25-29` importa `handoff_crypto`. `audit_runner.py:27` importa `scan_path` de `gate_ast`. *O problema real é outro:* a integração existe, mas é **silenciosa e opcional** (C-05) |
| 10 | BUG-01: `whisper_to_remotion.py` com indentação fatal e uso de `OPENAI_API_KEY` | ❌ | O arquivo converte TSV para JSON, sem rede (`:25-88`), e passa no `ast.parse`. *Bug real, não citado:* a heurística de unidade ms/s (M-13) |
| 11 | BUG-02: `sync_all.sh` tem 3 nomes legados e `sync_all.ps1` esquece o stitch | ❌ | Os dois iteram dinamicamente sobre os diretórios com `SKILL.md`. *Problema real:* `sync_all.ps1` é destrutivo (A-12) |
| 12 | BUG-03: `aidd-materialize-tutorial-stitch` ausente do `TAXONOMY.json` | ❌ | Está registrada (`TAXONOMY.json`, chave `skills.aidd-materialize-tutorial-stitch`). *Problema real:* a taxonomia usa os nomes novos e os pipelines usam os antigos (C-01) |
| 13 | BUG-04: o `requirements.txt` da raiz só tem `edge-tts` | 🟡 | Ele tem `pytest`, `pytest-cov`, `yt-dlp`, `pydantic` e `requests`, **sem** `edge-tts`. É verdade que faltam `edge-tts`, `Pillow`, `jsonschema` e `playwright`, e que vários `requirements.txt` de skill estão vazios (M-16) |
| 14 | BUG-05: binários de runtime versionados | ✅ | ~28 MB de `.mp4/.wav/.mp3` versionados, além de `state.json`, `context/handoffs` e `context/output` (M-15) |

### 2.3 Achados reais (ordenados por severidade)

#### 🔴 C-01 — Os pipelines referenciam skills que não existem (nomes legados)

- **Evidência:** `aidd-pipelines/canal-dark-avatar/PIPELINE.json` usa `aidd-dark-storycraft`, `aidd-remotion-motion` e `aidd-video-materializer`. `aidd-pipelines/video-to-tutorial/PIPELINE.json` usa `aidd-video-reengineer`, `aidd-skill-creator` e `aidd-remotion-motion`. Nenhum desses diretórios existe em `aidd-skills/`. Os nomes canônicos são `aidd-craft-story-ptbr`, `aidd-motion-remotion-core`, `aidd-materialize-video-synth`, `aidd-rea-video-youtube` e `aidd-orchestrate-skill-creator`.
- **Causa-raiz:** **a própria fábrica gera os nomes antigos.** `pipeline_creator.py:365,373,381,666` escreve `aidd-video-reengineer`, `aidd-skill-creator` e `aidd-remotion-motion` nos `PIPELINE.json` que cria. O manifesto `aidd-ouroboros/dependencies.json` também lista `aidd-video-reengineer`, `aidd-skill-swarm`, `aidd-dark-storycraft` etc.
- **Reprodução (VERIFICADO):**
  ```text
  $ python aidd-pipelines/canal-dark-avatar/run_pipeline.py ; echo $?
  [ERRO ZERO MOCKS] Script funcional da skill 'aidd-dark-storycraft' não localizado em …\aidd-skills\aidd-dark-storycraft.
  1
  ```
- **Impacto:** nenhum pipeline do repositório consegue executar um único nó real.

#### 🔴 C-02 — `state.json` versionado produz sucesso falso com selo criptográfico

- **Evidência:** `aidd-pipelines/video-to-tutorial/state.json` está versionado com os três nós `COMPLETED`. O runner pula nós `COMPLETED` (`run_pipeline.py:107-109`) e depois emite `pipeline_output.json` assinado com `status: "SUCCESS"` (`:220-232`), apontando para o `final_delivery_handoff.json` que também está versionado.
- **Reprodução (VERIFICADO):** exit `0`, 3 linhas `SKIP` e `payload.status == "SUCCESS"`, sem executar nenhuma skill.
- **Agravante:** o `state.json` de `canal-dark-avatar` é incoerente: `status: "COMPLETED"` no topo, todos os nós `PENDING` e três **nós-fantasma** (`node-01-ingest`, `node-02-creator`, `node-03-executor`) que não existem no `PIPELINE.json` dele.
- **Impacto:** é o pior tipo de falha para um sistema que vende determinismo: **mente, e com assinatura**.

#### 🔴 C-03 — Dois contratos de handoff incompatíveis, e a assinatura quebra o consumidor

- **Formato A (skills/schema):** `HANDOFF.schema.json:5` exige `$schema`, `producer_skill`, `status`, `artifacts` e `domain_data`. É o que `dark_storycraft.py:173-184` e `remotion_motion.py:31-47` emitem.
- **Formato B (cripto):** `criar_envelope_handoff` produz `{envelope_format, signature_algorithm, hmac_sha256, payload:{schema_version, producer_skill, timestamp, status, artifacts_pointers, domain_metadata}}` (`handoff_crypto.py:77-92`).
- **A colisão:** depois de cada nó, o runner **substitui** o arquivo de saída do Formato A por um envelope B e enterra o original em `payload.domain_metadata.original` (`run_pipeline.py:190-196`). O nó seguinte recebe B, mas as skills leem A: `envelope.get("artifacts", {})` (`dark_storycraft.py:28-29`) volta vazio. Além disso, **nenhum arquivo assinado valida contra o schema**.
- **Impacto:** mesmo corrigindo C-01, a cadeia de dados se rompe no segundo nó.

#### 🔴 C-04 — O "selo criptográfico" usa chave pública embutida

- `handoff_crypto.py:24`: `DEFAULT_SECRET = "aidd-secret-penny-harness-2026"`, usado como padrão em todas as funções (`:38,53,105`). O repositório é público, então a assinatura pode ser forjada por qualquer pessoa.
- `:134` compara com `!=` (não é tempo-constante). É um risco menor no uso local, mas é o padrão errado.
- **Impacto:** o selo não oferece autenticidade e só detecta corrupção acidental, o que um SHA-256 simples já faria sem dar falsa sensação de segurança.

#### 🔴 C-05 — Governança que se desliga em silêncio

- `run_pipeline.py:25-29`: se o import falhar, `criar_envelope_handoff = None` e o pipeline segue **sem** verificação nem assinatura, sem aviso.
- `:136`: a verificação só acontece se o campo `hmac_sha256` estiver presente (é opcional).
- `:146-147`: uma exceção na verificação vira `[WARN]` e o pipeline segue.
- `:198-199`: `except Exception: pass` na assinatura de saída.
- **Impacto:** todas as garantias anunciadas no cabeçalho ("Zero Mocks / HMAC-SHA256 Integrity", `:5`) são *best effort* e podem sumir sem rastro.

#### 🔴 C-06 — Fallbacks que fabricam dados (o verdadeiro "teatro")

| Arquivo | Trecho | O que fabrica |
|:--|:--|:--|
| `aidd-rea-app-android/scripts/app_reengineer.py` | `:212-216` | Se a entrada não é APK/ZIP/binário, inventa URLs (`https://api.app.com/v1`), permissões e *activities* (`MainActivity`, `LoginActivity`…) |
| idem | `:218-221` | **Mesmo depois de um scan real**, se não encontrou permissões ou *activities*, injeta valores fictícios. Dado real e inventado se misturam sem nenhuma marcação |
| `aidd-rea-social-carousel/scripts/social_reengineer.py` | `:206-212` | Pasta sem imagens → 4 slides inventados ("Como automatizar agentes com IA sem codigo"…) |
| `aidd-materialize-video-synth/scripts/video_materializer.py` | `:138-158` | Remotion falhou → cartão com texto fixo "Google Flow Storyboard Studio (Remotion 60fps)", `returncode` ignorado, devolvido como sucesso |
| idem | `:84-96` | TTS falhou → áudio sintetizado por ffmpeg, `returncode` ignorado (`:94`) |
| idem | `:286-287` | Avatar ausente → `avatar_placeholder.jpg` (a prova está versionada em `canal-dark-avatar/context/output/`) |

**Impacto:** quem consome esses handoffs não tem como saber o que é evidência e o que é ficção. É exatamente o que a Lei Zero-Stub queria impedir, e o `gate_ast` não detecta.

#### 🔴 C-07 — Stubs puros (os dois que de fato existem)

- `aidd-motion-remotion-core/scripts/remotion_motion.py` (78 linhas): não invoca o Remotion. Grava `fps: 60`, `resolution: [1920,1080]` e `scenes_ready: ["cena-02-conceito-remotion"]` fixos (`:31-47`). `check_doctor`, `run_setup` e `run_audit` só imprimem sucesso (`:12-26`). O motor real existe em `motores/remotion/` e está desconectado.
- `aidd-craft-story-ptbr/scripts/dark_storycraft.py`: o roteiro é constante (`:50-122`). A entrada é lida e ignorada. O `--doctor` e o `--audit` imprimem "OK" (`:162-168`).

#### 🟠 A-08 — `gate_ast` é cego para os padrões que deveria barrar

- Só verifica funções cujo corpo é exatamente `pass`, `...` ou `raise NotImplementedError` (`gate_ast.py:54-92`).
- Não visita `ExceptHandler`, não lê comentários (a AST os descarta) e não detecta funções que só imprimem e retornam uma constante.
- **VERIFICADO:** `gate_ast.py .` → "Todos os 52 arquivos atendem…". `gate_ast.py remotion_motion.py` → SUCESSO.

#### 🟠 A-09 — O runner escolhe o script da skill por ordem do sistema de arquivos

- `run_pipeline.py:157-159`: `scripts = list((skill_dir / "scripts").glob("*.py")); script_file = scripts[0]`.
- A ordem de `glob` depende do sistema de arquivos (no NTFS costuma ser alfabética; no ext4, não). Para `aidd-materialize-tutorial-stitch` (`capture.py`, `compose.py`, `explore.py`, `tutorial.py`), o runner rodaria `capture.py`, que não é o entrypoint.

#### 🟠 A-10 — Contrato CLI heterogêneo entre skills e runner

| Skill (entrypoint) | Interface atual | Compatível com o runner (`--input`, `--output-handoff`)? |
|:--|:--|:--:|
| `dark_storycraft.py` | `--input`, `--output-handoff` | ✅ |
| `remotion_motion.py` | `--input`, `--output-handoff` | ✅ (mas é stub) |
| `video_reengineer.py` | alvo posicional, `--output-handoff`, `--output-dir` | ❌ (`--input` não existe) |
| `rea_router.py` | posicional, `--target`, `--route`, `--output-handoff` | ❌ |
| `tutorial.py` | subcomandos (`produzir`, `render`, `compose`…) | ❌ (precisa de adapter) |
| `social_reengineer.py` / `app_reengineer.py` | `--input`, `--output-dir`, `--output-handoff` | ✅ (o `--output-dir` tem padrão) |

#### 🟠 A-11 — O kernel "autopoiético" não existe como código

- `ouroboros.py` é um despachante com `--doctor`, `--audit`, `--setup`, `--pipeline` e `--force` (`:134-138`). Não recebe objetivo, não roteia e não cria pipelines.
- `run_ouroboros.py:108` declara `--github-scout`, mas `main()` nunca trata a opção (`:112-124`): é uma flag morta.
- Os dois "doctors" discordam: `tesseract` e `yt-dlp` são **críticos** em `run_ouroboros.py:24-25` e **opcionais** em `ouroboros.py:35-36`.

#### 🟠 A-12 — `sync_all.ps1` apaga diretórios do usuário sem verificar a posse

- `:4` `SilentlyContinue`, `:7-19` lista de 11 nomes, `:35` `Remove-Item -Recurse -Force` em 13 diretórios de harness.
- Não verifica se o diretório foi criado pelo próprio sync (não há marcador) e não tem `-WhatIf`.
- **Impacto:** perda irreversível de skills homônimas criadas pelo usuário ou por outras ferramentas.

#### 🟡 M-13 — `whisper_to_remotion.py` interpreta milissegundos como segundos

- `:16-22`: se `valor > 1000`, divide por 1000; caso contrário, assume segundos. O TSV do Whisper usa **milissegundos inteiros**, então todo timestamp abaixo de 1000 ms vira segundos.
- **Reprodução (VERIFICADO):** TSV `0→840` e `840→2300` gera `0.0→840.0 s` e `840.0→2.3 s` (o fim fica antes do início) e `totalDurationInFrames = 50400` (14 min) para 2,3 s de áudio.

#### 🟡 M-14 — Testes verdes não cobrem a integração

- `pytest` → **90 passed** (VERIFICADO), enquanto os dois pipelines estão quebrados (C-01/C-02).
- `test_ouroboros_meta_pipeline.py` verifica se arquivos existem e checa a autoria da licença. Nenhum teste executa `run_pipeline.py` com as skills reais do almoxarifado.

#### 🟡 M-15 — Higiene do repositório

- ~28 MB de mídia versionada (`tests/smoke/renders/*.mp4`, `tests/smoke/audio/*.wav`, `canal-dark-avatar/context/output/*.mp4`…).
- Runtime versionado: 2× `state.json`, 12 arquivos em `context/{input,handoffs,output}` (inclusive `.mp4`, `.mp3` e `avatar_placeholder.jpg`) e `tests/smoke/composition/.hyperframes/video-state.json`.
- O `.gitignore` não cobre `workspace/`, `aidd-pipelines/*/state.json` nem `aidd-pipelines/*/context/`.

#### 🟡 M-16 — Dependências incompletas

- O `requirements.txt` da raiz não tem `edge-tts`, `Pillow`, `jsonschema` nem `playwright`.
- Os `requirements.txt` de `craft-story-ptbr`, `materialize-video-synth`, `motion-remotion-core`, `rea-app-android` e `rea-router` estão vazios. `materialize-video-synth` depende de `edge-tts` e de binários (`ffmpeg`, `bun`) que não estão declarados como verificáveis.

#### 🔵 B-17 — `audit_runner.py`: detalhes de robustez

- `:102` banner fixo "BRANCH feature-matt-penny".
- `:100` usa `root = Path.cwd()`: rodado de outra pasta, audita a pasta errada (o módulo já calcula `root_dir` a partir de `__file__` em `:23`).
- `:133` o gate de `AGENTS.md` não aborta a execução e termina com exit 2. Um CI que trate "≠0" como falha vai reprovar, mas um script que só olhe `== 1` não.

### 2.4 O que está bom (e deve ser preservado)

- **`aidd-materialize-tutorial-stitch`**: engenharia real e madura (≈3,9 mil linhas em `tutorial.py`, com captura, composição, TTS, legendas, render e vitrine) e testes de regressão (`tests/smoke`, `tests/negative*`).
- **`video_reengineer.py`**: pipeline REA real (yt-dlp → áudio → Whisper → frames → OCR).
- **Ordenação topológica com detecção de ciclo** no runner (`run_pipeline.py:62-86`).
- **Ideia de *pointer passing* com SHA-256 dos artefatos** (`handoff_crypto.py:59-75`): ótima para economizar tokens. Só precisa da correção de contrato e de chave.
- **Taxonomia formal** com padrão de nome por regex e `compatible_downstream`: é a base certa para o roteamento universal.

---

## PARTE 3 — Arquitetura-alvo revisada

### 3.1 Contrato único de handoff (resolve C-03, C-04, C-05)

```json
{
  "body": {
    "$schema": "aidd/handoff-v2",
    "producer_skill": "aidd-craft-story-ptbr",
    "producer_version": "1.1.0",
    "run_id": "2026-10-25T12-00-00Z-ab12",
    "status": "SUCCESS | PARTIAL | FAILED",
    "degraded": false,
    "degraded_reasons": [],
    "artifacts": { "roteiro": { "path": "…", "sha256": "…", "bytes": 1234 } },
    "domain_data": { }
  },
  "seal": {
    "alg": "HMAC-SHA256",
    "key_id": "env:AIDD_HANDOFF_KEY",
    "mac": "…",
    "canonicalization": "json-sort-keys-utf8"
  }
}
```

Regras:

1. O selo é calculado **sobre o `body` canônico** e **nunca o modifica**.
2. Ordem no runner: skill escreve `body` → validar o schema → selar → (próximo nó) verificar o selo → validar o schema → entregar o `body` à skill.
3. Chave obrigatória via env. Se faltar: `exit 2` com mensagem clara. Nenhum padrão embutido.
4. `status: PARTIAL` aceita `degraded: true` só se `degraded_reasons` não estiver vazio. O pipeline decide pela política (`allow_partial: false` por padrão) se segue ou não.
5. **Modelo de ameaça declarado:** HMAC protege contra corrupção e adulteração por quem **não tem** a chave. Para handoffs que cruzam máquinas ou pessoas, use Ed25519 (`cryptography`), com chave pública no repo e privada fora.

### 3.2 Manifesto de skill com entrypoint e aliases (resolve C-01, A-09, A-10)

Cada `aidd-skills/<skill>/dependencies.json` ganha:

```json
{
  "entrypoint": "scripts/dark_storycraft.py",
  "cli_contract": "aidd-pipeline-cli/v1",
  "binaries": [{"name": "ffmpeg", "min_version": "6.0"}],
  "python": ["edge-tts==6.1.12"],
  "env": ["AIDD_HANDOFF_KEY"]
}
```

E o `TAXONOMY.json` ganha um mapa único de aliases legados, usado pelo runner e pelo `pipeline_creator`. Resolver o alias gera um *warning*; um nome desconhecido gera **erro**:

```json
"aliases": {
  "aidd-dark-storycraft": "aidd-craft-story-ptbr",
  "aidd-remotion-motion": "aidd-motion-remotion-core",
  "aidd-video-materializer": "aidd-materialize-video-synth",
  "aidd-video-reengineer": "aidd-rea-video-youtube",
  "aidd-skill-creator": "aidd-orchestrate-skill-creator",
  "aidd-pipeline-creator": "aidd-orchestrate-pipeline-creator",
  "aidd-tutorial-creator": "aidd-materialize-tutorial-stitch"
}
```

### 3.3 Workspace por execução e resume honesto (resolve C-02, M-15)

- Todo runtime vai para `workspace/<pipeline_id>/<run_id>/{state.json, handoffs/, output/, evidence/}`.
- `--resume <run_id>` pula um nó **somente se** `sha256(entradas do nó + versão da skill + parâmetros)` for igual ao registrado.
- `aidd-pipelines/<p>/` passa a conter **só a definição** (`PIPELINE.json`, docs, fixtures de exemplo em `examples/`).

### 3.4 Gates com prova negativa (resolve A-08 e o Motivo 3)

- `motores/governanca/gate_ast.py` v2 passa a detectar: (a) os casos atuais; (b) `ExceptHandler` com corpo só `pass`/`...`; (c) `TODO|FIXME|XXX|HACK` via `tokenize`; (d) funções nomeadas `doctor|audit|check|verify*` cujo corpo não tem nenhuma chamada além de `print`/`log` e que retornam uma constante verdadeira.
- `tests/gates/fixtures/bad_*.py`: um arquivo por regra, que **deve** reprovar. `tests/gates/fixtures/good_*.py` **deve** passar.
- `--baseline gate_baseline.json`: permite a adoção gradual (violações já existentes ficam listadas e congeladas; qualquer violação **nova** reprova). A baseline só pode **diminuir**, nunca crescer.

### 3.5 Política de fallback honesto (resolve C-06)

| Situação | Proibido | Obrigatório |
|:--|:--|:--|
| Ferramenta ausente | Inventar dados plausíveis | `status: PARTIAL`, `degraded_reasons: ["yt-dlp ausente"]`, campos de domínio vazios/`null` |
| Subprocesso falhou | Ignorar o `returncode` | `check=True` ou ramo explícito, stderr no handoff, exit ≠ 0 se a saída física não existir |
| Render de mídia falhou | Gerar cartão/placeholder como se fosse o produto | Falhar. Placeholder só com `--allow-placeholder` explícito, e então `degraded: true` |

### 3.6 Kernel universal (resolve A-11). **Só depois de 3.1–3.5**

```
ouroboros.py --goal "<texto>" [--target <alvo>] [--dry-run] [--yes]
  1. Formaliza o objetivo (6 vetores) → workspace/<run_id>/GOAL.json (validado por schema)
  2. Classifica o alvo (rea_router --classify) → tipo
  3. Seleciona o pipeline por TAXONOMY.input_types/compatible_downstream (sem if/else de nomes)
  4. Se não existir: pipeline_creator (nomes canônicos) → PIPELINE.json validado
  5. dependency_resolver --check (e --install só com --yes, versões fixadas)
  6. run_pipeline --workspace workspace/<run_id>
  7. audit: verificar selos + schema + critério de pronto (vetor 6)
  --dry-run para no passo 5 e imprime o plano em JSON.
```

---

## PARTE 4 — Plano de ação: nano-tickets v2

**Como ler:** cada ticket tem objetivo, arquivos, ação e um *Binary Gate*. **Regra de aceite universal:** o gate deve **falhar antes** e **passar depois**, e as duas saídas são anexadas ao PR. A coluna "Falha hoje?" diz se isso foi conferido nesta auditoria.

> Comandos em `bash` (Git Bash no Windows). `$PY` = interpretador Python do projeto.

### 📦 ÉPICO 0 — Parar a mentira e o dano (prioridade máxima)

#### 🎫 NT-01 — Tirar runtime e mídia do git e fechar o `.gitignore`

- **Resolve:** C-02, M-15.
- **Arquivos:** `.gitignore`; remoção do índice (`git rm --cached`) de `aidd-pipelines/*/state.json`, `aidd-pipelines/*/context/**`, `tests/smoke/composition/.hyperframes/video-state.json`; mídia de teste → regenerada pelo teste ou movida para Git LFS; nova `tests/FIXTURES_ALLOWLIST.txt` (arquivos binários deliberadamente versionados).
- **Ação:**
  1. `.gitignore` += `workspace/`, `aidd-pipelines/*/state.json`, `aidd-pipelines/*/context/`, `**/.hyperframes/video-state.json`, `*.mp4`, `*.wav`, `*.mp3` (com exceções `!` para a allowlist).
  2. Mover os exemplos de entrada úteis para `aidd-pipelines/<p>/examples/input.json`.
- **Binary Gate:**
  ```bash
  $PY -c "import subprocess,re,sys,pathlib
  allow=set(pathlib.Path('tests/FIXTURES_ALLOWLIST.txt').read_text().split()) if pathlib.Path('tests/FIXTURES_ALLOWLIST.txt').exists() else set()
  files=subprocess.run(['git','ls-files'],capture_output=True,text=True).stdout.split()
  bad=[f for f in files if f not in allow and (re.search(r'(^|/)state\.json$|/context/(input|handoffs|output)/|\.(mp4|wav|mp3)$',f))]
  print('\n'.join(bad)); sys.exit(1 if bad else 0)"
  ```
- **Falha hoje?** ✅ Sim (VERIFICADO: 31 arquivos: 2 `state.json`, 12 arquivos em `context/` e 17 mídias fora de `context/`).

#### 🎫 NT-02 — Desarmar o `sync_all.ps1` destrutivo

- **Resolve:** A-12.
- **Arquivos:** `aidd-skills/sync_all.ps1`, todos os `aidd-skills/*/sync.ps1` e `sync.sh`; novo `tests/test_sync_safety.py`.
- **Ação:**
  1. Todo `sync.*` grava `.aidd-managed` (com nome canônico e hash da origem) no diretório de destino.
  2. A limpeza de legados só remove diretórios **que contenham `.aidd-managed`**. Os demais são listados como "conflito, não removido".
  3. `$ErrorActionPreference = "Stop"`, parâmetro `-HarnessRoot` (padrão `$HOME`) e `-WhatIf` respeitado.
- **Binary Gate:**
  ```bash
  $PY -m pytest -q tests/test_sync_safety.py
  ```
  O teste cria `tmp/.claude/skills/aidd-skill-creator/` **sem** marcador e outro diretório **com** marcador, roda `powershell -File sync_all.ps1 -HarnessRoot tmp` e verifica que só o marcado foi removido.
- **Falha hoje?** ✅ Sim, por construção (o script não aceita `-HarnessRoot` e apaga sem marcador).

#### 🎫 NT-03 — Chave do selo fora do código e verificação fail-closed

- **Resolve:** C-04, C-05.
- **Arquivos:** `motores/governanca/handoff_crypto.py`, `aidd-skills/aidd-orchestrate-pipeline-creator/templates/RUN_PIPELINE_TEMPLATE.py` (e a propagação para os `run_pipeline.py`), `tests/test_handoff_crypto.py`.
- **Ação:**
  1. Remover `DEFAULT_SECRET`. Criar `obter_chave()`, que lê `AIDD_HANDOFF_KEY` e lança `RuntimeError` se estiver ausente.
  2. Trocar `!=` por `hmac.compare_digest`.
  3. No runner: remover o `try/except ImportError` (`:25-29`) e o `except Exception: pass` (`:198-199`). Exigir o selo quando `PIPELINE.json` tiver `"require_seal": true` (padrão `true`).
  4. CLI: sem subcomando → `exit 2`.
- **Binary Gate:**
  ```bash
  ! grep -rn "DEFAULT_SECRET\|aidd-secret-penny" motores aidd-skills aidd-pipelines \
  && $PY -m pytest -q tests/test_handoff_crypto.py
  ```
  O teste cobre: sem chave → erro; payload alterado → falha; campo `seal` removido com `require_seal` → falha; chave errada → falha.
- **Falha hoje?** ✅ Sim (o `grep` encontra `handoff_crypto.py:24`).

### 📦 ÉPICO 1 — Um contrato, nomes canônicos, entrypoints explícitos

#### 🎫 NT-04 — Nomes canônicos em todos os pipelines e na fábrica

- **Resolve:** C-01.
- **Arquivos:** `aidd-pipelines/*/PIPELINE.json`, `aidd-skills/aidd-orchestrate-pipeline-creator/scripts/pipeline_creator.py` (`:365,373,381,666`), `aidd-ouroboros/dependencies.json`, `aidd-skills/TAXONOMY.json` (+`aliases`).
- **Ação:** substituir os nomes legados pelos canônicos, adicionar `aliases` (§3.2) e fazer o runner e o `pipeline_creator` resolverem aliases com *warning* e nomes desconhecidos com **erro**.
- **Binary Gate:**
  ```bash
  $PY -c "import json,glob,sys
  t=json.load(open('aidd-skills/TAXONOMY.json',encoding='utf-8'))['skills']
  bad=[(p,n['skill']) for p in glob.glob('aidd-pipelines/*/PIPELINE.json') for n in json.load(open(p,encoding='utf-8'))['nodes'] if n['skill'] not in t]
  src=open('aidd-skills/aidd-orchestrate-pipeline-creator/scripts/pipeline_creator.py',encoding='utf-8').read()
  bad+=[('pipeline_creator.py',l) for l in ['aidd-video-reengineer','aidd-skill-creator','aidd-remotion-motion','aidd-dark-storycraft','aidd-video-materializer'] if '\"'+l+'\"' in src]
  print(bad); sys.exit(1 if bad else 0)"
  ```
- **Falha hoje?** ✅ Sim (6 nós inválidos e 3 literais legados no `pipeline_creator`).

#### 🎫 NT-05 — Contrato único `body` + `seal`

- **Resolve:** C-03.
- **Arquivos:** `aidd-ouroboros/schemas/HANDOFF.schema.json` (v2: `body`, com `degraded` e `degraded_reasons`), `motores/governanca/handoff_crypto.py` (`selar(body) -> envelope`, `abrir(envelope) -> body`), runner/template, `requirements.txt` (+`jsonschema`), `tests/test_handoff_contract.py`.
- **Ação:** o runner nunca reembrulha a saída da skill. Sela o `body` em um envelope e entrega à próxima skill o caminho de um `body` verificado (ou o envelope com o `body` intacto, e as skills leem `body`).
- **Binary Gate:**
  ```bash
  $PY -m pytest -q tests/test_handoff_contract.py
  ```
  O teste: a skill A grava `body` com `artifacts.x`; o runner sela; a skill B (fixture) lê e afirma `artifacts.x` presente; o arquivo selado valida contra o schema v2.
- **Falha hoje?** ✅ Sim (C-03: o envelope atual não valida contra o schema, e `artifacts` vem vazio para o consumidor).

#### 🎫 NT-06 — Entrypoint explícito e contrato CLI padrão

- **Resolve:** A-09, A-10.
- **Arquivos:** `aidd-skills/*/dependencies.json` (+`entrypoint`, `cli_contract`), runner/template (remover `glob("*.py")[0]`), adapters: `aidd-rea-video-youtube/scripts/pipeline_adapter.py`, `aidd-rea-router/scripts/pipeline_adapter.py`, `aidd-materialize-tutorial-stitch/scripts/pipeline_adapter.py` (este chama `tutorial.py produzir` a partir do `body`).
- **Binary Gate:**
  ```bash
  ! grep -nF 'glob("*.py")' aidd-skills/aidd-orchestrate-pipeline-creator/templates/RUN_PIPELINE_TEMPLATE.py aidd-pipelines/*/run_pipeline.py \
  && $PY -c "import json,glob,subprocess,sys,os
  bad=[]
  for d in glob.glob('aidd-skills/aidd-*/dependencies.json'):
      m=json.load(open(d,encoding='utf-8')); ep=m.get('entrypoint')
      if not ep: bad.append((d,'sem entrypoint')); continue
      h=subprocess.run([sys.executable,os.path.join(os.path.dirname(d),ep),'--help'],capture_output=True,text=True).stdout
      if '--input' not in h or '--output-handoff' not in h: bad.append((d,'CLI fora do contrato'))
  print(bad); sys.exit(1 if bad else 0)"
  ```
- **Falha hoje?** ✅ Sim (o `glob` está presente em `run_pipeline.py:157`, e nenhum manifesto tem `entrypoint`).

### 📦 ÉPICO 2 — Gates que mordem

#### 🎫 NT-07 — `gate_ast` v2 com fixtures negativos e baseline

- **Resolve:** A-08, Motivo 3, Motivo 4.
- **Arquivos:** `motores/governanca/gate_ast.py`, `tests/gates/fixtures/{bad_except_pass.py, bad_todo_comment.py, bad_fake_doctor.py, bad_pass_body.py, good_real.py}`, `motores/governanca/gate_baseline.json`, `tests/test_gate_ast.py`.
- **Ação:** implementar as regras (a)–(d) da §3.4 e `--baseline`. Gerar a baseline atual (inclusive os ≥11 `except: pass`) e congelá-la.
- **Binary Gate:**
  ```bash
  for f in tests/gates/fixtures/bad_*.py; do $PY motores/governanca/gate_ast.py "$f" >/dev/null 2>&1 && { echo "GATE NÃO MORDEU: $f"; exit 1; }; done; \
  $PY motores/governanca/gate_ast.py tests/gates/fixtures/good_real.py \
  && $PY motores/governanca/gate_ast.py . --baseline motores/governanca/gate_baseline.json
  ```
- **Falha hoje?** ✅ Sim (VERIFICADO: o `gate_ast` atual aprova um `except: pass` e funções de `doctor` falsas).

#### 🎫 NT-08 — Teste E2E de pipeline com skills reais

- **Resolve:** M-14.
- **Arquivos:** `aidd-pipelines/_e2e-smoke/PIPELINE.json` (ex.: `aidd-rea-router` → `aidd-rea-app-android` sobre um ZIP-fixture com `AndroidManifest.xml` em texto), `tests/e2e/test_pipeline_real.py` (marcador `e2e`).
- **Binary Gate:**
  ```bash
  AIDD_HANDOFF_KEY=test $PY -m pytest -q -m e2e tests/e2e
  ```
  Afirma: exit 0, `state.json` no `workspace/`, um handoff selado por nó, `body.domain_data` derivado do fixture (as permissões declaradas no manifesto-fixture aparecem; nenhuma permissão inventada aparece).
- **Falha hoje?** ✅ Sim (não há como rodar um pipeline real hoje, por C-01, C-03 e A-10).

### 📦 ÉPICO 3 — Erradicar stubs e fallbacks mentirosos

#### 🎫 NT-09 — Fallback honesto nas skills REA e no materializador

- **Resolve:** C-06.
- **Arquivos:** `app_reengineer.py` (`:212-221`), `social_reengineer.py` (`:206-212`), `video_materializer.py` (`:84-96`, `:138-158`, `:286-287`).
- **Ação:** apagar os dados inventados. Sem evidência → listas vazias + `status: PARTIAL` + `degraded_reasons`. Todo `subprocess.run` com `check=True`. Placeholder só com `--allow-placeholder`.
- **Binary Gate:**
  ```bash
  ! grep -n "api.app.com\|LoginActivity\|Como automatizar agentes com IA sem codigo\|Storyboard Studio (Remotion" \
      aidd-skills/aidd-rea-app-android/scripts/app_reengineer.py \
      aidd-skills/aidd-rea-social-carousel/scripts/social_reengineer.py \
      aidd-skills/aidd-materialize-video-synth/scripts/video_materializer.py \
  && $PY -m pytest -q tests/test_honest_fallback.py
  ```
  O teste: `app_reengineer` sobre um `.txt` qualquer → `permissions == []` e `status == "PARTIAL"`; o materializador com `ffmpeg` fora do `PATH` → exit ≠ 0.
- **Falha hoje?** ✅ Sim (o `grep` encontra as três strings).

#### 🎫 NT-10 — `remotion_motion.py` real (motor `motores/remotion`)

- **Resolve:** C-07 (parte 1).
- **Ação:** gerar `props.json` a partir do `body` do roteiro, rodar `bunx remotion render src/index.ts Main <out.mp4> --props props.json` (ou `npx`), com `check=True`, e verificar com `ffprobe`. `doctor` checa de verdade `bun|npx`, `node_modules` e `ffprobe`. Sem Remotion → exit ≠ 0 (sem placeholder).
- **Binary Gate:**
  ```bash
  AIDD_HANDOFF_KEY=test $PY -m pytest -q tests/test_remotion_motion_real.py
  ```
  Com o motor presente: `ffprobe` mostra `codec_name=h264`, duração > 0, e a duração bate com a soma das cenas do roteiro (±1 frame). Com `PATH` sem `bun`/`npx`: exit ≠ 0 e nenhum `.mp4` criado.
- **Falha hoje?** ✅ Sim (o script atual não produz `.mp4`).

#### 🎫 NT-11 — `dark_storycraft.py` híbrido e contido

- **Resolve:** C-07 (parte 2).
- **Ação:** separar (a) a parte **determinística**, que extrai hook, ritmo e duração do handoff REA e monta o *prompt* a partir de um template versionado; (b) a parte **probabilística**, que chama o LLM (provedor configurável) e devolve JSON; (c) o **gate**, que valida contra `ROTEIRO.schema.json` (cenas, tempos, idioma, ausência de placeholders). O modo `--offline` só gera o *prompt* e sai com `PARTIAL`.
- **Binary Gate:**
  ```bash
  $PY -m pytest -q tests/test_storycraft_contract.py
  ```
  Dois handoffs de entrada diferentes → dois *prompts* com hashes diferentes. Uma resposta-fixture do LLM inválida → reprovada pelo schema. Uma resposta-fixture válida → aprovada.
- **Falha hoje?** ✅ Sim (saída idêntica para qualquer entrada).

#### 🎫 NT-12 — Unidade de tempo no `whisper_to_remotion.py`

- **Resolve:** M-13.
- **Ação:** `--units {ms,s,auto}` (padrão `ms` para TSV do Whisper). `auto` só infere pela presença de ponto decimal **na coluna inteira**, nunca por linha. Validar `end >= start` (senão: erro com o número da linha).
- **Binary Gate:**
  ```bash
  printf 'start\tend\ttext\n0\t840\toi\n840\t2300\tola\n' > /tmp/t.tsv \
  && $PY scripts/whisper_to_remotion.py -i /tmp/t.tsv -o /tmp/p.json \
  && $PY -c "import json,sys;e=json.load(open('/tmp/p.json'))['events'];sys.exit(0 if (e[0]['endSeconds'],e[1]['startSeconds'],e[1]['endSeconds'])==(0.84,0.84,2.3) else 1)"
  ```
- **Falha hoje?** ✅ Sim (VERIFICADO: gera `840.0`, `840.0` e `2.3`).

### 📦 ÉPICO 4 — Estado, dependências e kernel universal

#### 🎫 NT-13 — Workspace por `run_id` e resume por hash

- **Resolve:** C-02 (estrutural).
- **Ação:** o runner aceita `--workspace` e `--resume <run_id>`. Grava `inputs_hash` por nó e só pula nó com hash igual.
- **Binary Gate:**
  ```bash
  AIDD_HANDOFF_KEY=test $PY -m pytest -q tests/test_resume_integrity.py
  ```
  O teste roda, altera a entrada e roda com `--resume`: o nó afetado **re-executa**. Um `state.json` "COMPLETED" falso, colocado à mão, **não** gera `SUCCESS`.

#### 🎫 NT-14 — `dependency_resolver.py` com política de aquisição

- **Resolve:** M-16, Motivo 5.
- **Ação:** ler os `dependencies.json` (§3.2) das skills do pipeline. `--check` → relatório JSON (`READY`/`MISSING`, por item). `--install` exige `--yes` e só instala itens com versão fixada de fonte oficial. Variáveis de ambiente são verificadas **por nome**, sem nunca imprimir o valor.
- **Binary Gate:**
  ```bash
  $PY -m pytest -q tests/test_dependency_resolver.py
  ```
  Binário inexistente → `MISSING` e exit ≠ 0. `--install` sem `--yes` → recusa. Item sem versão fixada → recusa. A saída nunca contém o valor de uma variável de ambiente-fixture.

#### 🎫 NT-15 — Kernel `ouroboros.py --goal/--target` (com `--dry-run`)

- **Resolve:** A-11.
- **Pré-requisitos:** NT-03 a NT-08 e NT-13/14 concluídos.
- **Ação:** o fluxo da §3.6. A seleção de pipeline usa `TAXONOMY.input_types` e `compatible_downstream`, sem `if` de nomes. Remover a flag morta `--github-scout` de `run_ouroboros.py` (ou implementá-la) e unificar os dois `doctor` numa só fonte (`dependencies.json`).
- **Binary Gate:**
  ```bash
  $PY ouroboros.py --goal "Dissecar app Android" --target tests/e2e/fixtures/app.zip --dry-run > /tmp/plan.json \
  && $PY -c "import json,jsonschema;jsonschema.validate(json.load(open('/tmp/plan.json')),json.load(open('aidd-ouroboros/schemas/PLAN.schema.json')))" \
  && grep -q '"aidd-rea-app-android"' /tmp/plan.json
  ```

#### 🎫 NT-16 — Robustez do `audit_runner.py`

- **Resolve:** B-17.
- **Ação:** `root` a partir de `__file__` (com `--root` opcional), banner sem nome de branch fixo, flag `--print-root`, códigos de saída documentados (`0` ok, `1` gate bloqueante, `2` pendência não bloqueante) e incorporar NT-07 (baseline) e a verificação de selos/schema de um `--workspace`.
- **Binary Gate:**
  ```bash
  REPO="$(pwd -P)"; \
  out="$(cd "$(mktemp -d)" && $PY "$REPO/motores/governanca/audit_runner.py" --print-root)"; \
  test "$($PY -c "import os,sys;print(os.path.realpath(sys.argv[1]))" "$out")" = "$($PY -c "import os,sys;print(os.path.realpath(sys.argv[1]))" "$REPO")" \
  && ! grep -n "feature-matt-penny" motores/governanca/audit_runner.py
  ```
- **Falha hoje?** ✅ Sim (`--print-root` não existe, e o banner fixo está em `audit_runner.py:102`).

### Ordem de execução e dependências

```
NT-01 ─┐
NT-02 ─┼─► NT-04 ─► NT-05 ─► NT-06 ─► NT-08 ─► NT-13 ─► NT-15
NT-03 ─┘              ▲                 ▲        NT-14 ─┘
              NT-07 ──┴── (gates valem p/ todo o resto)
                       NT-09, NT-10, NT-11, NT-12 (paralelos após NT-05/06)
                       NT-16 (a qualquer momento após NT-07)
```

---

## PARTE 5 — Rastreabilidade v1 → v2

| Ticket v1 | Destino na v2 | Motivo |
|:--|:--|:--|
| NT-01 (taxonomia + sync dinâmico) | **Descartado** e substituído por NT-04 (nomes canônicos) e NT-02 (sync seguro) | A taxonomia e o sync já estavam corretos. O gate dava `KeyError` |
| NT-02 (audit_runner + schema + cripto) | **Reescrito** em NT-03, NT-05 e NT-16 | Funções citadas inexistentes. A validação de schema contradizia o envelope. Gate vazio |
| NT-03 (assinar entre etapas) | **Invertido** em NT-05 | O runner já assina, e é isso que quebra o contrato. A correção é selar sem reembrulhar |
| NT-04 (dependency_resolver) | **Mantido e endurecido** em NT-14 | Ideia certa. Ganha política de aquisição, versões fixadas e `--yes` |
| NT-05 (router + kernel) | **Adiado** para NT-15 | O alvo era imaginário (`if canal-dark-avatar`). O kernel depende da fundação |
| NT-06 (adapter stitch) | **Absorvido** em NT-06 | Generalizado: entrypoint explícito + adapters para todas as skills fora do contrato |
| NT-07 (`video_reengineer` real) | **Descartado** e substituído por adapter (NT-06) | O script já é real. Faltava só a compatibilidade de CLI |
| NT-08 (whisper + bytes nulos) | **Reescrito** em NT-12 e NT-10 | Os dois bugs citados não existem. Há um bug real de unidade e o stub real do Remotion. A recomendação de fallback com lavfi foi **rejeitada** |
| NT-09 (REA web/app/social reais) | **Reescrito** em NT-09 | Já são reais. O problema é a fabricação nos fallbacks |
| NT-10 (`.gitignore`) | **Mantido e ampliado** em NT-01 | Ganha remoção do índice, allowlist e um gate binário de verdade |
| — | **Novos:** NT-07, NT-08, NT-11, NT-13, NT-16 | Gates que reprovam, E2E real, storycraft híbrido, resume honesto, robustez da auditoria |

---

## Apêndice A — Comandos de reprodução

Execute numa **cópia descartável** do clone, porque os pipelines escrevem `state.json` e `context/`.

```bash
git clone https://github.com/heverton-dev/aidd-ouroboros.git repo && cd repo
git rev-parse HEAD   # 8e877822583f709a188c7787076f6afa9b90734f

# C-01 — pipeline morre no nó 1
(cd aidd-pipelines/canal-dark-avatar && python run_pipeline.py; echo "exit=$?")

# C-02 — sucesso falso assinado sem executar nada
(cd aidd-pipelines/video-to-tutorial && python run_pipeline.py | grep -c SKIP; echo "exit=$?")

# A-08 — gate_ast aprova stubs
python motores/governanca/gate_ast.py aidd-skills/aidd-motion-remotion-core/scripts/remotion_motion.py
python motores/governanca/gate_ast.py .

# C-04 — chave embutida
grep -n DEFAULT_SECRET motores/governanca/handoff_crypto.py

# Motivo 3 — gates da v1
python -c "import json; json.load(open('aidd-skills/TAXONOMY.json',encoding='utf-8'))['categories']"   # KeyError
python motores/governanca/handoff_crypto.py; echo "exit=$?"                                          # 0 (vazio)
python ouroboros.py --target x --goal y                                                              # unrecognized arguments

# M-13 — unidade de tempo
printf 'start\tend\ttext\n0\t840\toi\n840\t2300\tola\n' > t.tsv && python scripts/whisper_to_remotion.py -i t.tsv -o p.json && cat p.json

# M-14 — testes verdes apesar dos pipelines quebrados
python -m pytest -q --ignore=tests/negative --ignore=tests/negative-brand   # 90 passed
```

---

*Fim da v2. Na próxima revisão deste documento, as mesmas regras se aplicam a ele: cada afirmação precisa de evidência, e qualquer trecho que não se sustentar ao ser re-executado deve ser corrigido ou retirado.*
