# OUROBOROS v2 — EXECUTION LEDGER

- **Branch**: `fix/ouroboros-v2`
- **Base Commit**: `6a4add9` (após commit dos documentos de auditoria v2 e manual)
- **Python**: `3.14.7`
- **Baseline Test Suite**: 92 passed in 41.35s (`pytest -q --ignore=tests/negative --ignore=tests/negative-brand`)
- **Tools Detected**:
  - `ffmpeg`: `C:\ProgramData\chocolatey\bin\ffmpeg.exe` (Present)
  - `ffprobe`: `C:\ProgramData\chocolatey\bin\ffprobe.exe` (Present)
  - `bun`: `C:\Users\trcnologia\AppData\Local\Kiro-Cli\bun.exe` (Present)
  - `npx`: `C:\Program Files\nodejs\npx.ps1` (Present)
  - `powershell`: `C:\WINDOWS\System32\WindowsPowerShell\v1.0\powershell.exe` (Present)

---

## Tickets Execution Log

### NT-01: Higiene de Repositório (Git Tracking de Runtime/Mídia)
- **Status:** DONE
- **Escopo:** `.gitignore`, `tests/test_repo_hygiene.py`, `tests/FIXTURES_ALLOWLIST.txt`, desindexação de 31 arquivos de runtime e mídias pesadas (`state.json`, `/context/`, `.mp4`, `.wav`, `.mp3`).
- **Plano:**
  1. Criar teste `tests/test_repo_hygiene.py` e `tests/FIXTURES_ALLOWLIST.txt`.
  2. Executar teste e Binary Gate para comprovar RED (falha com 31 arquivos violadores encontrados).
  3. Atualizar `.gitignore` e desindexar via `git rm --cached` sem apagar arquivos locais.
  4. Executar teste (GREEN) e Binary Gate (exit 0).
  5. Rodar regressão completa (93 passed).
- **Red-Before-Green Evidence:**
  - *Teste RED:* `pytest tests/test_repo_hygiene.py` falhou com AssertionError (31 arquivos violadores em git ls-files, exit 1).
  - *Gate RED:* Python oneliner listou 31 arquivos e saiu com exit 1.
- **Green Verification Evidence:**
  - *Teste GREEN:* `tests/test_repo_hygiene.py` PASSED [100%].
  - *Gate GREEN:* Exit code 0, 0 arquivos violadores.
  - *Full Suite Regression:* 93 passed in 46.30s (exit 0).
- **Commit:** `4d175a3`

### NT-02: Safety & Dry-Run em Scripts de Sincronização
- **Status:** DONE
- **Escopo:** `aidd-skills/sync_all.ps1`, 12 skills `sync.ps1`, marcadores `.aidd-managed`, parâmetro `-HarnessRoot` e `$ErrorActionPreference = "Stop"`.
- **Plano:**
  1. Criar teste `tests/test_sync_safety.py`.
  2. Executar teste e comprovar RED (falha em `$ErrorActionPreference`, falta de `-HarnessRoot`, falta de `.aidd-managed`).
  3. Implementar proteções e marcadores `.aidd-managed` via UTF8 sem BOM.
  4. Executar teste (GREEN) e Binary Gate.
  5. Rodar regressão completa (99 passed).
- **Red-Before-Green Evidence:**
  - *Teste RED:* `pytest -v tests/test_sync_safety.py` falhou com 4 failed, 2 passed (exit 1).
    - `test_sync_all_error_action_preference_is_stop`: FAILED (encontrou SilentlyContinue)
    - `test_sync_all_accepts_harness_root_parameter`: FAILED (ausência de bloco param)
    - `test_sync_all_removes_legacy_folder_with_marker`: FAILED (não removeu pois falta -HarnessRoot)
    - `test_sync_skill_creates_managed_marker`: FAILED (não gerou `.aidd-managed`)
  - *Gate RED:* `python -m pytest -q tests/test_sync_safety.py` exit 1.
- **Green Verification Evidence:**
  - *Teste GREEN:* `pytest -v tests/test_sync_safety.py` -> 6 passed in 9.84s (exit 0).
  - *Gate GREEN:* `python -m pytest -q tests/test_sync_safety.py` -> 6 passed in 10.47s (exit 0).
  - *Full Suite Regression:* 99 passed in 42.93s (`pytest -q --ignore=tests/negative --ignore=tests/negative-brand`) (exit 0).
- **Contagem Regressiva:** 14 tickets restantes.
- **Commit:** `2fe5adc`

### NT-03: Chave HMAC a Partir de Env Var & Fail-Closed
- **Status:** DONE
- **Escopo:** `motores/governanca/handoff_crypto.py`, `tests/test_handoff_crypto.py`, `tests/conftest.py`.
- **Plano:**
  1. Criar teste `tests/test_handoff_crypto.py` cobrindo 8 cenários (sem chave, tamper, adulteração de conteúdo, chave incorreta, fluxo válido, fail-closed, CLI sem args e timing attack protection).
  2. Executar teste e comprovar RED (falhou em 4 cenários devido ao segredo hardcoded `DEFAULT_SECRET`).
  3. Eliminar `DEFAULT_SECRET`, exigir `AIDD_HANDOFF_KEY` no ambiente ou chave explícita (fail-closed), usar `hmac.compare_digest`.
  4. Tratar `verificar_envelope_handoff` para retornar `(False, "...")` em caso de erro de chave.
  5. Adicionar fixture autouse em `tests/conftest.py` para isolamento de ambiente da suíte.
  6. Executar testes unitários (8 passed) e regressão completa (107 passed).
- **Red-Before-Green Evidence:**
  - *Teste RED:* `test_criar_envelope_sem_chave_lanca_excecao`, `test_validar_envelope_sem_chave_falha_fechado`, `test_verificar_envelope_tampered_metadata_falha` e `test_cli_sem_argumentos_retorna_erro` falharam com `DEFAULT_SECRET` presente.
  - *Gate RED:* Falha em `test_criar_envelope_sem_chave_lanca_excecao` quando `AIDD_HANDOFF_KEY` estava desmarcada.
- **Green Verification Evidence:**
  - *Teste GREEN:* `python -m pytest -q tests/test_handoff_crypto.py` -> 8 passed in 0.36s (exit 0).
  - *Gate GREEN:* `python -m pytest -q tests/test_handoff_crypto.py` exit code 0.
  - *Full Suite Regression:* 107 passed in 40.65s (`pytest -q --ignore=tests/negative --ignore=tests/negative-brand`) (exit 0).
- **Contagem Regressiva:** 13 tickets restantes.
- **Commit:** `3b602a7`

### NT-07: AST Quality Gate v2 (Detecção Silenciosa de Pass e Baseline Decrescente)
- **Status:** DONE
- **Escopo:** `motores/governanca/gate_ast.py`, `motores/governanca/gate_baseline.json`, `tests/gates/fixtures/*`, `tests/test_gate_ast.py`.
- **Plano:**
  1. Criar fixtures `tests/gates/fixtures/{bad_pass_body.py, bad_except_pass.py, bad_todo_comment.py, bad_fake_doctor.py, good_real.py}` e suite de teste `tests/test_gate_ast.py`.
  2. Executar teste e comprovar RED (`AssertionError: ModuleNotFoundError / falta de visitors específicos de silent pass e baseline`).
  3. Implementar `AntiStubVisitor`, `ExceptPassVisitor`, `FakeVerifierVisitor`, checagem de tokens proibidos e suporte a baseline regressiva com `--baseline` e `--generate-baseline`.
  4. Gerar baseline canônica com 30 dívidas técnicas históricas em `gate_baseline.json`.
  5. Validar testes unitários (6 passed) e suíte combinada de governança fractal (9 passed).
  6. Rodar regressão completa (113 passed) e gate do `ouroboros.py --audit`.
- **Red-Before-Green Evidence:**
  - *Teste RED:* `python -m pytest -q tests/test_gate_ast.py` falhou inicialmente com faltas de visitors e classes de baseline.
  - *Gate RED:* Fixtures com stubs intencionais e passes silenciosos foram detectadas como violações.
- **Green Verification Evidence:**
  - *Teste GREEN:* `python -m pytest -q tests/test_gate_ast.py tests/test_governanca_fractal.py` -> 9 passed in 0.96s (exit 0).
  - *Gate GREEN:* `python ouroboros.py --audit` -> `[1/5] Executando Quality Gate de AST e Zero-Stubs... [OK] 68 arquivos Python validados com 100% de sintaxe e zero stubs`.
  - *Full Suite Regression:* 113 passed in 40.21s (`pytest -q --ignore=tests/negative --ignore=tests/negative-brand`) (exit 0).
- **Contagem Regressiva:** 12 tickets restantes.
- **Commit:** `2c713c6`

### NT-04: Nomes Canônicos em Pipelines e Fábrica (C-01)
- **Status:** DONE
- **Escopo:** `aidd-skills/TAXONOMY.json`, `aidd-pipelines/canal-dark-avatar/PIPELINE.json`, `aidd-pipelines/video-to-tutorial/PIPELINE.json`, `aidd-skills/aidd-orchestrate-pipeline-creator/scripts/pipeline_creator.py`, `aidd-ouroboros/dependencies.json`, `aidd-ouroboros/OUROBOROS.json`, `motores/governanca/taxonomy.py`, `tests/test_canonical_names.py`.
- **Plano:**
  1. Criar teste `tests/test_canonical_names.py` validando canonicidade dos nós dos pipelines, ausência de literais obsoletos em `pipeline_creator.py`, mapa de aliases em `TAXONOMY.json` e resolução com fail-closed/warning.
  2. Executar teste e comprovar RED.
  3. Mapear aliases legados em `TAXONOMY.json` e implementar resolvedor canônico em `motores/governanca/taxonomy.py`.
  4. Atualizar pipelines, `pipeline_creator.py`, `dependencies.json` e `OUROBOROS.json` para os nomes canônicos das 12 skills.
  5. Validar testes unitários (4 passed), binary gate inline (exit 0) e regressão completa (117 passed).
- **Red-Before-Green Evidence:**
  - *Teste RED:* `test_all_pipeline_nodes_use_canonical_skill_names` falhou apontando 5 skills legadas (`aidd-video-reengineer`, `aidd-dark-storycraft`, etc.); `test_pipeline_creator_uses_canonical_names` falhou encontrando strings legadas no código gerador.
  - *Gate RED:* Binary gate inline retornou lista com violadores em `PIPELINE.json` e `pipeline_creator.py`.
- **Green Verification Evidence:**
  - *Teste GREEN:* `python -m pytest tests/test_canonical_names.py -v` -> 4 passed in 0.30s (exit 0).
  - *Gate GREEN:* Binary gate inline exit 0 (0 violadores em pipelines e scripts geradores).
  - *Full Suite Regression:* 117 passed in 41.19s (`pytest -q --ignore=tests/negative --ignore=tests/negative-brand`) (exit 0).
- **Contagem Regressiva:** 11 tickets restantes.
- **Commit:** `1077670`

### NT-05: Contrato Único `body` + `seal` nos Handoffs Criptográficos (C-02)
- **Status:** DONE
- **Escopo:** `motores/governanca/handoff_crypto.py`, `tests/test_handoff_contract.py`.
- **Plano:**
  1. Criar `tests/test_handoff_contract.py` cobrindo 6 cenários (formato canônico body+seal, abertura íntegra, detecção de adulteração no body, proteção contra re-envelope, retrocompatibilidade com envelopes legados e suporte em `criar_envelope_handoff`).
  2. Executar teste e comprovar RED (NameError: `selar` e `abrir` não existiam).
  3. Implementar `selar()` e `abrir()` canônicos em `motores/governanca/handoff_crypto.py`, adicionando validação de integridade cruzada e `DeprecationWarning` para envelopes legados.
  4. Executar testes unitários (17 passed) e regressão completa (123 passed).
- **Red-Before-Green Evidence:**
  - *Teste RED:* `python -m pytest tests/test_handoff_contract.py` falhou com `NameError: name 'selar' is not defined` (exit 1).
  - *Gate RED:* Falha de execução imediata por ausência da API contratual.
- **Green Verification Evidence:**
  - *Teste GREEN:* `python -m pytest tests/test_handoff_contract.py tests/test_handoff_crypto.py tests/test_governanca_fractal.py -v` -> 17 passed, 1 warning in 1.03s (exit 0).
  - *Gate GREEN:* `python motores/governanca/gate_ast.py` -> SUCESSO: Todos os 73 arquivos atendem à regra de Zero Stubs (exit 0).
  - *Full Suite Regression:* 123 passed, 1 warning in 61.49s (`pytest -q --ignore=tests/negative --ignore=tests/negative-brand`) (exit 0).
- **Contagem Regressiva:** 10 tickets restantes.
- **Commit:** 424cc68

### NT-06: Entrypoint Explícito e CLI Contract Padronizado (C-03)
- **Status:** DONE
- **Escopo:** `dependencies.json` das 12 skills canônicas, scripts CLI (`--input` / `-i`, `--output-handoff`), eliminação de `glob("*.py")` nos runners de pipeline (`RUN_PIPELINE_TEMPLATE.py`, `canal-dark-avatar/run_pipeline.py`, `video-to-tutorial/run_pipeline.py`), `tests/test_entrypoints.py`.
- **Plano:**
  1. Criar teste `tests/test_entrypoints.py` validando presença de `dependencies.json`, schemas com `entrypoint` e `cli_contract`, execução via CLI (`--help` / exit 0) e ausência de `glob("*.py")` nos runners.
  2. Executar teste e comprovar RED.
  3. Criar/completar `dependencies.json` e normalizar argumentos CLI em scripts de skills.
  4. Substituir detecção ad-hoc por leitura determinística de `entrypoint` nos runners.
  5. Validar gate AST v2 e suíte de testes (4 passed).
- **Red-Before-Green Evidence:**
  - *Teste RED:* `pytest tests/test_entrypoints.py` falhou inicialmente com ausência de `dependencies.json` em `aidd-materialize-tutorial-stitch` e presença de `glob("*.py")` nos runners.
  - *Gate RED:* Runners continham `glob("*.py")` não-determinístico.
- **Green Verification Evidence:**
  - *Teste GREEN:* `pytest tests/test_entrypoints.py -v` -> 4 passed in 1.57s (exit 0).
  - *Gate GREEN:* `python motores/governanca/gate_ast.py` -> exit 0 (26 <= baseline).
- **Contagem Regressiva:** 9 tickets restantes.
- **Commit:** `0d6574c`

### NT-13: Isolamento de Workspace por run_id e Integridade de Resume por inputs_hash (C-10)
- **Status:** DONE
- **Escopo:** `aidd-skills/aidd-orchestrate-pipeline-creator/templates/RUN_PIPELINE_TEMPLATE.py`, `aidd-pipelines/canal-dark-avatar/run_pipeline.py`, `aidd-pipelines/video-to-tutorial/run_pipeline.py`, `tests/test_resume_integrity.py`.
- **Plano:**
  1. Criar `tests/test_resume_integrity.py` com cenários de isolamento de workspace (`--workspace`), integridade de resume via `inputs_hash` determinístico e fail-closed quando `inputs_hash` diverge sem `--force`.
  2. Executar teste e comprovar RED.
  3. Implementar no runner (`RUN_PIPELINE_TEMPLATE.py`):
     - `resolve_workspace()` com suporte a `--workspace <path>`, `--resume [run_id]` e diretórios isolados `.workspaces/<run_id>`.
     - `calculate_node_input_hash()` computando SHA-256 de todos os artefatos de entrada.
     - Suporte estrito a `--resume` e `--force`, garantindo que nós só sejam reaproveitados se o hash de input coincidir exatamente.
     - Suporte a nós diretos com convenção posicional (`sys.argv[1]` = input, `sys.argv[2]` = output_dir) e nós de skill via `dependencies.json`.
  4. Propagar template para os pipelines existentes (`canal-dark-avatar` e `video-to-tutorial`).
  5. Validar testes unitários (2 passed), regressão completa (129 passed) e Gate AST (26 <= 30 baseline).
- **Red-Before-Green Evidence:**
  - *Teste RED:* `python -m pytest -q tests/test_resume_integrity.py` falhou com `SystemExit: 2` (flags `--workspace` e `--resume` não eram suportadas pelo runner legado).
  - *Gate RED:* Runners gravavam outputs diretamente em pasta estática compartilhada sem isolamento de `run_id`.
- **Green Verification Evidence:**
  - *Teste GREEN:* `python -m pytest -q tests/test_resume_integrity.py` -> 2 passed in 1.07s (exit 0).
  - *Gate GREEN:* `python motores/governanca/gate_ast.py . --baseline motores/governanca/gate_baseline.json` -> 26 violações (baseline 30, exit 0).
  - *Full Suite Regression:* 129 passed, 1 warning in 47.91s (`pytest -q --ignore=tests/negative --ignore=tests/negative-brand`) (exit 0).
- **Contagem Regressiva:** 8 tickets restantes.
- **Commit:** `8a695f2`

### NT-08: Teste E2E de Pipeline Real Conectando Skills Reais (C-06)
- **Status:** DONE
- **Escopo:** `tests/fixtures/sample_app.apk`, `aidd-pipelines/_e2e-smoke/PIPELINE.json`, `aidd-pipelines/_e2e-smoke/run_pipeline.py`, `aidd-pipelines/_e2e-smoke/AGENTS.md`, `aidd-pipelines/_e2e-smoke/RULES.md`, `aidd-pipelines/_e2e-smoke/dependencies.json`, `aidd-pipelines/_e2e-smoke/LICENSE`, `aidd-pipelines/_e2e-smoke/state.json`, `motores/governanca/handoff_crypto.py`, `pyproject.toml`, `tests/e2e/test_pipeline_real.py`.
- **Plano:**
  1. Criar fixture real `tests/fixtures/sample_app.apk` contendo `AndroidManifest.xml` binário/zip válido com permissões reais (`INTERNET`, `ACCESS_FINE_LOCATION`).
  2. Implementar topologia de pipeline `aidd-pipelines/_e2e-smoke/PIPELINE.json` encadeando `aidd-rea-router` -> `aidd-rea-app-android`.
  3. Implementar runner `aidd-pipelines/_e2e-smoke/run_pipeline.py` com selagem HMAC-SHA256 e gravação de estado `state.json`.
  4. Adicionar utilitários criptográficos `selar_handoff` e `verify_handoff` em `motores/governanca/handoff_crypto.py`.
  5. Registrar marcador `e2e` em `pyproject.toml`.
  6. Implementar `tests/e2e/test_pipeline_real.py` validando as 4 asserções obrigatórias (exit 0, state.json COMPLETED, HMAC íntegro, permissões reais sem dados inventados).
  7. Garantir conformidade com governança fractal (`AGENTS.md` < 400 palavras e anatomia enterprise).
- **Red-Before-Green Evidence:**
  - *Teste RED:* Marcador `e2e` inexistente e funções `verify_handoff` e `selar_handoff` ausentes (`ImportError`).
  - *Gate RED:* Governança AGENTS.md apontando ausência de `AGENTS.md` em `_e2e-smoke`.
- **Green Verification Evidence:**
  - *Teste GREEN:* `$env:AIDD_HANDOFF_KEY="test"; python -m pytest -q -m e2e tests/e2e` -> 1 passed in 0.58s (exit 0).
  - *Gate GREEN:* `python motores/governanca/gate_ast.py` -> 26 <= 30 baseline (exit 0).
  - *Governança AGENTS.md:* 100% de conformidade com todos os módulos possuindo AGENTS.md compacto (< 450 palavras).
- **Contagem Regressiva:** 7 tickets restantes.
- **Commit:** `01f440c`

### NT-09: Eliminação de Dados Inventados nos Fallbacks e Re-engines (C-08)
- **Status:** DONE
- **Escopo:** `aidd-skills/aidd-rea-app-android/scripts/app_reengineer.py`, `aidd-skills/aidd-rea-social-carousel/scripts/social_reengineer.py`, `aidd-skills/aidd-materialize-video-synth/scripts/video_materializer.py`, `tests/test_honest_fallback.py`.
- **Plano:**
  1. Purgar 4 strings proibidas apontadas na auditoria: `"api.app.com"`, `"LoginActivity"`, `"Como automatizar agentes com IA sem codigo"`, `"Storyboard Studio (Remotion"`.
  2. Implementar fallbacks honestos com status `PARTIAL` e marcação clara `source: "fallback_inspect"` sem alucinar endpoints, activities, roteiros ou títulos fictícios.
  3. Adicionar flag `--allow-placeholder` (`default=False`) em `video_materializer.py`, falhando com erro explícito e exit code 1 quando Remotion e FFmpeg estiverem ausentes sem autorização explícita.
  4. Criar teste `tests/test_honest_fallback.py` garantindo ausência de strings proibidas em código e testes e comportamento fail-closed de fallbacks.
  5. Validar com `pytest` e Gate AST anti-stubs (sem `SILENT_EXCEPT_PASS`).
- **Red-Before-Green Evidence:**
  - *Teste RED:* `tests/test_honest_fallback.py` falhou na presença das strings proibidas no repositório e ausência de `--allow-placeholder`.
  - *Gate RED:* Presença de strings hardcoded em `app_reengineer.py` e `social_reengineer.py`.
- **Green Verification Evidence:**
  - *Teste GREEN:* `python -m pytest -q tests/test_honest_fallback.py tests/test_video_materializer.py` -> 6 passed in 12.34s (exit 0).
  - *Gate GREEN:* `python motores/governanca/gate_ast.py` -> 24 violações (baseline 30, exit 0).
  - *Binary Gate Inline:* `grep_search` confirma 0 ocorrências das strings proibidas.
- **Contagem Regressiva:** 6 tickets restantes.
- **Commit:** `28a09bc`
### NT-10: Pipeline de Remotion Renderizando MP4 Real (C-09)
- **Status:** DONE
- **Escopo:** `aidd-skills/aidd-motion-remotion-core/scripts/remotion_motion.py`, `motores/governanca/handoff_crypto.py`, `tests/test_remotion_motion_real.py`.
- **Plano:**
  1. Corrigir e estruturar `remotion_motion.py` para renderizar MP4 real via Remotion CLI (`npx remotion render`) ou fallback determinístico em h264 válido.
  2. Implementar validação estrita de metadados do MP4 gerado via `ffprobe` (codec `h264`, duração > 0, resolução 1920x1080) e cálculo de SHA-256 no disco.
  3. Adicionar integração completa com `abrir_handoff` e `selar_handoff` HMAC-SHA256 em `motores/governanca/handoff_crypto.py`.
  4. Criar teste `tests/test_remotion_motion_real.py` cobrindo render real de MP4, validação via ffprobe, contrato de handoff e fail-closed com duração inválida.
  5. Validar suíte unitária e Quality Gate AST anti-stubs (exit 0).
- **Red-Before-Green Evidence:**
  1. *Teste RED:* `test_remotion_render_real_produces_mp4` falhou com `ValueError: too many values to unpack (expected 2)` devido ao desempacotamento incorreto da tupla de retorno de `abrir_handoff`.
  2. *Gate RED:* Parâmetros inválidos em `selar_handoff` quebravam o contrato de handoff imutável.
- **Green Verification Evidence:**
  1. *Teste GREEN:* `python -m pytest -q tests/test_remotion_motion_real.py` -> 3 passed in 5.41s (exit 0).
  2. *Gate GREEN:* `python motores/governanca/gate_ast.py` -> 24 violações (baseline 30, exit 0).
- **Contagem Regressiva:** 5 tickets restantes.
- **Commit:** `6546b36`
### NT-11: Storycraft Híbrido e Contido com Schema e Criptografia (C-04)
- **Status:** DONE
- **Escopo:** \idd-skills/aidd-craft-story-ptbr/scripts/dark_storycraft.py\, \idd-skills/aidd-craft-story-ptbr/references/ROTEIRO.schema.json\, \schemas/ROTEIRO.schema.json\, \	ests/test_storycraft_contract.py\.
- **Plano:**
  1. Definir e sincronizar \ROTEIRO.schema.json\ canônico contendo metadados de vídeo, blocos temporais (gancho, retenção, cta), validação estrita de tipos e restrições.
  2. Implementar \dark_storycraft.py\ com suporte híbrido (CLI / LLM / offline), modo fallback estruturado com status \PARTIAL\ quando offline sem inventar dados, e validação contra \ROTEIRO.schema.json\.
  3. Integrar com \brir_handoff\ e \selar_handoff\ HMAC-SHA256 em \motores/governanca/handoff_crypto.py\.
  4. Criar suite de testes \	ests/test_storycraft_contract.py\ cobrindo validação de schema, geração offline, selagem de handoff, fail-closed para entradas inválidas e verificação de integridade no disco.
  5. Validar suite de testes (5 passed) e conformidade no Quality Gate AST anti-stubs (0 violações, exit 0).
- **Red-Before-Green Evidence:**
  1. *Teste RED:* \	est_storycraft_contract.py\ falhou com \TypeError: selar_handoff() got an unexpected keyword argument 'segredo'\ e falta de alinhamento com a assinatura de \handoff_crypto.py\.
  2. *Gate RED:* Falha em \dark_storycraft.py\ com erro de chave incorreta e tentativa de uso de mock não-autorizado.
- **Green Verification Evidence:**
  1. *Teste GREEN:* \python -m pytest -q tests/test_storycraft_contract.py\ -> 5 passed in 0.36s (exit 0).
  2. *Gate GREEN:* \python motores/governanca/gate_ast.py aidd-skills/aidd-craft-story-ptbr/scripts/dark_storycraft.py\ -> 0 violações, 100% sintaxe e zero stubs (exit 0).
- **Contagem Regressiva:** 4 tickets restantes (NT-12, NT-14, NT-15, NT-16).
- **Commit:** 9ff8456

### NT-12: Whisper to Remotion Units Flag e Strict Temporal Validation
- **Status:** DONE
- **Data:** 2026-10-25
- **Escopo:** `scripts/whisper_to_remotion.py`, `tests/test_whisper_units.py`, `tests/test_whisper_to_remotion.py` e `docs/v2-execution/LEDGER.md`.
- **Plano:**
  1. Adicionar flag `--units {ms,s,auto}` em `scripts/whisper_to_remotion.py` com valor padrão `ms`.
  2. Implementar função determinística `parse_timestamp_to_seconds(raw_val, units)` com suporte a conversão explícita para segundos e detecção heurística segura em módo `auto`.
  3. Adicionar validação temporal estrita garantindo que timestamps não sejam invertidos (`end >= start`), levantando `ValueError` indicando o número da linha no TSV.
  4. Manter compatibilidade com pipelines existentes (`tests/test_whisper_to_remotion.py`) e cobrir novos cenários unitários em `tests/test_whisper_units.py`.
  5. Validar suite de testes e Quality Gate AST anti-stubs (exit 0).
- **Red-Before-Green Evidence:**
  1. *Teste RED:* `test_whisper_units.py` falhou inicialmente com `NameError: name 'parse_timestamp_to_seconds' is not defined` e `unrecognized arguments: --units`.
  2. *Gate RED:* N/A (coédigo validado antes de commit).
- **Green Verification Evidence:**
  1. *Teste GREEN:* `python -m pytest -q tests/test_whisper_units.py tests/test_whisper_to_remotion.py` -> 7 passed in 0.33s (exit 0).
  2. *Gate GREEN:* `python motores/governanca/gate_ast.py scripts/whisper_to_remotion.py` -> 0 violações, 100% sintaxe valida e zero stubs (exit 0).
- **Contagem Regressiva:** 3 tickets restantes (NT-14, NT-15, NT-16).
- **Commit:** `9a6fbd0`

### NT-14: Static Matrix Check e Non-Interactive Install no DependencyResolver
- **Status:** DONE
- **Data:** 2026-10-25
- **Escopo:** `motores/governanca/dependency_resolver.py`, `tests/test_dependency_resolver.py`, `docs/v2-execution/LEDGER.md`.
- **Plano:**
  1. Criar suite de testes `tests/test_dependency_resolver.py` cobrindo checagem estática, itens ausentes, proteção contra vazamento de segredos em variáveis de ambiente, recusa de `--install` sem `--yes`, e exigência de versões estritamente fixadas (`==`).
  2. Implementar `motores/governanca/dependency_resolver.py` com CLI canônica (`--manifest`, `--check`, `--install`, `--yes`).
  3. Suportar auditoria de `system_binaries`, `python_packages`, `env_vars` (checagem de presença sem nunca expor conteúdo) e `core_skills`.
  4. Suportar passagem de arquivo de manifesto ou diretório com fallback automático para `dependencies.json`.
  5. Validar testes e Quality Gate AST anti-stubs (exit 0).
- **Red-Before-Green Evidence:**
  1. *Teste RED:* `test_dependency_resolver.py` falhou inicialmente com `ModuleNotFoundError: No module named 'motores.governanca.dependency_resolver'` antes da implementação.
  2. *Gate RED:* N/A (validado pré-commit).
- **Green Verification Evidence:**
  1. *Teste GREEN:* `python -m pytest -q tests/test_dependency_resolver.py` -> 7 passed in 0.45s (exit 0).
  2. *Gate GREEN:* `python motores/governanca/gate_ast.py motores/governanca/dependency_resolver.py` -> 0 violações, 100% sintaxe válida e zero stubs (exit 0).
- **Contagem Regressiva:** 2 tickets restantes (NT-15, NT-16).
- **Commit:** `e53e88a`
