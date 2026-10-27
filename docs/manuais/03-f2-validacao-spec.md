# Manual de Engenharia &bull; Etapa 3: Validação da SPEC

> **Raio-X de Arquitetura da Etapa 3 do Ouroboros**  
> Localização no pipeline: `1. ENTREVISTA ➔ 2. SPEC ➔ [3. VALIDAÇÃO DA SPEC] ➔ 4. REA ➔ 5. SKILLS ➔ 6. PIPELINE ➔ 7. DEPS ➔ 8. GATES ➔ 9. HANDOFF`

---

## 📊 Grau Geral de Automação da Etapa

```
[██████████████████████████████████████████████████] 100% Determinístico | 0% Probabilístico
```
- **100% Determinístico**: JSON Schema (Draft7), checagem de `approved` e detecção de placeholders — fail-closed, sem LLM.

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| `SPEC.json` | `Path` (CLI `--orchestrate`) | `./SPEC_PIPELINE.json` | Etapa 1 / 2 |
| `--output-dir` | `Path` | `./ouroboros-out` | CLI (default: cwd) |
| `--resume` | `bool` | após exit 3 | CLI |
| Chave HMAC | `env` | `OUROBOROS_CRYPTO_SECRET` | `.env` (para handoffs seguintes) |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 3.1: Existência e sintaxe JSON
- **O que faz**: Verifica arquivo no disco e `json.load`; erro → exit 1.
- **Natureza**: `100% Determinístico`.

### Ação 3.2: Validação JsonSchema
- **O que faz**: `jsonschema.Draft7Validator` contra `schemas/SPEC_PIPELINE.schema.json`; cada violação formatada `caminho: mensagem` → exit 1.
- **Natureza**: `100% Determinístico`.

### Ação 3.3: Travas de aprovação e placeholder
- **O que faz**: Se `approved != true` → exit 2. Se `user_request` contém `PREENCHER` ou `pipeline.name` for `placeholder-pipeline`/vazio → grava `pending_question.json` e exit 3.
- **Natureza**: `100% Determinístico`.

### Ação 3.4: Inicialização do runtime de execução
- **O que faz**: Cria `output-dir/handoffs`, fixa raiz de estado (`ouroboros_master_state.json` + `pending_question.json` no out_dir), marca `status: RUNNING`.
- **Natureza**: `100% Determinístico`.

---

## 3. Scripts, Funções e Regras no Código

- **Função**: `ouroboros_master.py` &bull; `orchestrate(spec_path, resume, out_dir)`.
- **Validadores**: `validate_spec` + `spec_is_placeholder`.
- **Schema**: `schemas/SPEC_PIPELINE.schema.json` (`additionalProperties: false`, `approved` boolean, `pipeline.steps` minItems 1).
- **Regra**: nenhuma etapa F2 roda se esta retornar exit 1, 2 ou 3.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **SPEC validada** | Próxima etapa F2 (REA) | Sinalização por exit code 0 + estado em memória |
| **State inicial** | Operador / mestre | `OUT/ouroboros_master_state.json` (`status: RUNNING`) |
| **Pergunta pendente** (exit 3) | Usuário (mini-entrevista) | `OUT/pending_question.json` |
| **Recusa de avanço** (exit 2) | Operador | Mensagem em stderr + código 2 |
