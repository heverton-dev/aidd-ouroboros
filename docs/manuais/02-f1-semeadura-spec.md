# Manual de Engenharia &bull; Etapa 2: Semeadura da SPEC

> **Raio-X de Arquitetura da Etapa 2 do Ouroboros**  
> Localização no pipeline: `1. ENTREVISTA ➔ [2. SEMEADURA DA SPEC] ➔ 3. F2 ORQUESTRAÇÃO ➔ 4. HANDOFF ➔ 5. RUNNER`

---

## 📊 Grau Geral de Automação da Etapa

```
[██████████████████████████████████████████████████] 100% Determinístico | 0% Probabilístico
```
- **100% Determinístico**: Hash do pedido, leitura de template e escrita de JSON — sem LLM, sem rede, sem aleatoriedade (apenas timestamp no `spec_id`/`created_at`).

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| `--from-nl` | `string` | `"criar pipeline demo a partir de https://example.com"` | CLI do operador |
| `--output-spec` | `Path` | `./SPEC_PIPELINE.json` | CLI (default: `./SPEC_PIPELINE.json`) |
| `--goal` | `string` | `"provar fluxo"` | CLI (opcional) |
| Template | `JSON` | `schemas/SPEC_PIPELINE.template.json` | Repositório |

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 2.1: Carregamento do template
- **O que faz**: Lê `SPEC_PIPELINE.template.json` (estrutura com placeholders e `approved: false`).
- **Natureza**: `100% Determinístico`.

### Ação 2.2: Geração do identificador canônico
- **O que faz**: `spec_id = "spec-" + sha256(user_request + timestamp_utc)[:16]`.
- **Natureza**: `100% Determinístico`.

### Ação 2.3: Preenchimento dos campos de cabeçalho
- **O que faz**: Grava `user_request`, `goal`, `created_at` (UTC) e força `approved: false`.
- **Natureza**: `100% Determinístico`.

### Ação 2.4: Persistência e anúncio
- **O que faz**: Escreve JSON indentado no caminho de `--output-spec`, imprime a SPEC no stdout e a instrução da F1 no stderr.
- **Natureza**: `100% Determinístico`.

---

## 3. Scripts, Funções e Regras no Código

- **Função**: `ouroboros_master.py` &bull; `cmd_init_spec(output, user_request, goal)`.
- **CLI espelho**: `ouroboros.py --from-nl` &bull; despacha para o script da mestra.
- **Template**: `schemas/SPEC_PIPELINE.template.json`.
- **Regra**: nunca seta `approved: true`; nunca remove placeholders (papel exclusivo da Etapa 1).

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **SPEC inicial** | Usuário / agente (F1) | Arquivo JSON em `--output-spec` + cópia no stdout |
| **Estado de bloqueio** | Etapa 3 (validação F2) | `approved: false` (impede orquestração prematura) |
| **Identificador estável** | Audição / logs | Campo `spec_id` |
