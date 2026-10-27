# Manual de Engenharia &bull; Etapa 10: Handoff Final (Envelope HMAC)

> **Raio-X de Arquitetura da Etapa 10 do Ouroboros**  
> Localização no pipeline: `8. DEPS ➔ 9. GATES ➔ [10. HANDOFF FINAL] ➔ 11. RUNNER`

---

## 📊 Grau Geral de Automação da Etapa

```
[██████████████████████████████████████████████████] 100% Determinístico | 0% Probabilístico
```
- **100% Determinístico**: SHA-256 dos artefatos apontados + HMAC-SHA256 canônico (JSON ordenado). Sem chave → não emite (fail-closed).

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| SPEC em memória | `dict` | campos `spec_id`, `user_request`, `pipeline` | Etapa 3 |
| State da F2 | `JSON` | `OUT/ouroboros_master_state.json` | Etapas 3–9 |
| `output-dir` | `Path` | `OUT/handoffs/` | CLI |
| **Chave HMAC** | `env` | `AIDD_HANDOFF_KEY` \| `OUROBOROS_HMAC_SECRET` \| `OUROBOROS_CRYPTO_SECRET` | `.env` / ambiente |
| Ponteiros de artefato | `paths` | `state_path`, `pipeline_dir` | State (se existirem em disco) |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 10.1: Resolução da chave
- **O que faz**: `ensure_hmac_env()` carrega `.env` e lê a variável de segredo. Ausente → `RuntimeError` (não assina envelope falso).
- **Natureza**: `100% Determinístico`.

### Ação 10.2: Montagem do payload
- **O que faz**: Define `status` (`SUCCESS` se audit OK, senão `PARTIAL`), hash SHA-256 dos artefatos existentes e metadados da SPEC/estágios.
- **Natureza**: `100% Determinístico`.

### Ação 10.3: Selo do envelope
- **O que faz**: `criar_envelope_handoff` → `selar(body)` com HMAC-SHA256; espelha `payload` + `hmac_sha256` no topo (retrocompat).
- **Natureza**: `100% Determinístico`.

### Ação 10.4: Persistência e limpeza
- **O que faz**: Grava `OUT/handoffs/master_final_handoff.json`; se audit OK, remove `pending_question.json` residual.
- **Natureza**: `100% Determinético`.

> **Paralelo da Etapa 4/5:** o handoff da REA (`01_rea_handoff.json`) usa o mesmo motor e é **verificado** antes desta etapa.

---

## 3. Scripts, Funções e Regras no Código

- **Função da mestra**: `ouroboros_master.py` &bull; `emit_final_handoff`, `ensure_hmac_env`.
- **Motor cripto**: `motores/governanca/handoff_crypto.py` &bull; `criar_envelope_handoff`, `selar`, `abrir`, `verify_handoff_envelope`.
- **Estrutura**: `envelope_format`, `body`, `seal`, espelho `payload`/`hmac_sha256`.
- **Regra**: pointer architecture — entrega ponteiros + hash, não despeja binários no chat.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **Envelope final da fabricação** | Usuário / auditoria / próximo pipeline (Lego) | `OUT/handoffs/master_final_handoff.json` (JSON HMAC) |
| **Status da corrida** | Operador | Campo `status` (SUCCESS/PARTIAL) + `spec_id` no stdout |
| **Verificabilidade** | Qualquer consumidor | `verify_handoff_envelope(path) == True` |
| **State fechado** | Operador / resume | `ouroboros_master_state.json` com `finished_at` |
