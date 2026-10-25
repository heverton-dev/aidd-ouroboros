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
- **Commit:** PENDENTE


