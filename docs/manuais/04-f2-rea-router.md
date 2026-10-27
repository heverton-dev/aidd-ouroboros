# Manual de Engenharia &bull; Etapa 4: Roteamento REA

> **Raio-X de Arquitetura da Etapa 4 do Ouroboros**  
> Localização no pipeline: `3. VALIDAÇÃO SPEC ➔ [4. ROTEAMENTO REA] ➔ 5. DISSECAÇÃO ➔ 6. SKILLS ➔ 7. PIPELINE ➔ 8. GATES`

---

## 📊 Grau Geral de Automação da Etapa

```
[██████████████████████████████████████████████████] 100% Determinístico | 0% Probabilístico
```
- **100% Determinístico**: Classificação por extensão, prefixo de URL e keywords. Sem rede na classificação; o despacho apenas executa o especialista (que pode ter rede).

---

## 1. Input da Etapa (O que entra e de onde vem)

| Dado | Tipo | Exemplo | Origem |
| :--- | :--- | :--- | :--- |
| `target.kind` | `enum` | `"web"` \| `"apk"` \| `"video"` \| `"social"` \| `"none"` | SPEC (Etapa 1) |
| `target.uri` / `path` | `string` | `https://example.com` ou `/app.apk` | SPEC |
| `--output-dir` (absoluto) | `Path` | `C:/.../OUT/rea` | Mestra F2 |
| `--output-handoff` (absoluto) | `Path` | `C:/.../OUT/handoffs/01_rea_handoff.json` | Mestra F2 |

> Se `target.kind == "none"`, a etapa inteira é **SKIPPED** (projeto do zero).

---

## 2. Processamento Passo a Passo (Microações e Natureza)

### Ação 4.1: Decisão de execução
- **O que faz**: Sem alvo → `SKIPPED`; com alvo → prossegue.
- **Natureza**: `100% Determinístico`.

### Ação 4.2: Classificação da mídia
- **O que faz**: Mapeia alvo → dissecador: `.apk`/binário → `aidd-rea-app-android`; `.mp4`/YouTube → `aidd-rea-video-youtube`; `http(s)` → `aidd-rea-web-saas`; slides/pasta → `aidd-rea-social-carousel`.
- **Natureza**: `100% Determinístico`.

### Ação 4.3: Despacho do especialista
- **O que faz**: `rea_router.py --target <uri> --output-dir <abs> --output-handoff <abs>` em subprocesso, cwd = raiz do repo.
- **Natureza**: `100% Determinístico` (orquestração); o trabalho pesado é da Etapa 5.

### Ação 4.4: Pré-checagem de saída
- **O que faz**: Exige rc=0, existência do handoff e **verificação HMAC** do envelope da REA. Falha → `pending_question.json` + exit 3.
- **Natureza**: `100% Determinístico`.

---

## 3. Scripts, Funções e Regras no Código

- **Função da mestra**: `ouroboros_master.py` &bull; `stage_rea`.
- **Script**: `aidd-skills/aidd-rea-router/scripts/rea_router.py` &bull; `classify_target`, `route_and_execute`.
- **Regra de caminho**: paths de saída **absolutos** (path relativo vaza para `aidd-skills/<skill>/...`).
- **Gates**: handoff deve verificar `verify_handoff_envelope == True`.

---

## 4. O que a Etapa Entrega, Para Quem e Como?

| O que entrega | Para quem entrega | Como entrega (Formato / Meio) |
| :--- | :--- | :--- |
| **Despacho** | Dissecador especialista (Etapa 5) | Subprocesso CLI com alvo + paths absolutos |
| **Estado da etapa** | Mestra / operador | `stages.rea = {status, handoff, hmac}` no state |
| **Handoff da REA** | Mestra (verificação) e downstream | `OUT/handoffs/01_rea_handoff.json` (HMAC) |
| **SKIP legítimo** | Mestra | `stages.rea = {status: SKIPPED}` se `kind=none` |
